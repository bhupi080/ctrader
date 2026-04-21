import threading
from typing import Any, Sequence, Type

from google.protobuf.message import Message
from twisted.internet import reactor

from ctrader_open_api import Client, EndPoints, Protobuf, TcpProtocol
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthReq,
    ProtoOAAccountAuthRes,
    ProtoOAApplicationAuthReq,
    ProtoOAApplicationAuthRes,
    ProtoOAErrorRes,
)

from app.core.config import Settings
from app.services.exceptions import CTraderApiError, CTraderServiceError, CTraderTimeoutError


class CTraderTransport:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        host_type = settings.ctrader_host.lower()
        host = EndPoints.PROTOBUF_LIVE_HOST if host_type == "live" else EndPoints.PROTOBUF_DEMO_HOST

        self.client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self._connected = threading.Event()
        self._started = threading.Event()
        self._connection_error: Exception | None = None
        self._authorized_account_ids: set[int] = set()
        self._auth_lock = threading.Lock()

        self.client.setConnectedCallback(self._on_connected)
        self.client.setDisconnectedCallback(self._on_disconnected)

    def start(self) -> None:
        if self._started.is_set():
            return

        reactor_thread = threading.Thread(
            target=reactor.run,
            kwargs={"installSignalHandlers": False},
            daemon=True,
            name="ctrader-reactor",
        )
        reactor_thread.start()

        self._run_in_reactor(self.client.startService)
        self._started.set()

        if not self._connected.wait(timeout=self.settings.ctrader_request_timeout_seconds):
            raise CTraderTimeoutError("Timed out while connecting to cTrader.")
        if self._connection_error:
            raise CTraderServiceError(str(self._connection_error))

    def stop(self) -> None:
        if not self._started.is_set():
            return
        self._run_in_reactor(self.client.stopService)
        if reactor.running:
            reactor.callFromThread(reactor.stop)

    def authenticate(self) -> None:
        app_req = ProtoOAApplicationAuthReq()
        app_req.clientId = self.settings.ctrader_client_id
        app_req.clientSecret = self.settings.ctrader_client_secret
        self.request(app_req, expected_types=(ProtoOAApplicationAuthRes,))
        self.ensure_account_authorized(self.settings.ctrader_account_id)

    def ensure_account_authorized(self, account_id: int) -> None:
        with self._auth_lock:
            if account_id in self._authorized_account_ids:
                return
            account_req = ProtoOAAccountAuthReq()
            account_req.ctidTraderAccountId = account_id
            account_req.accessToken = self.settings.ctrader_access_token
            self.request(account_req, expected_types=(ProtoOAAccountAuthRes,))
            self._authorized_account_ids.add(account_id)

    def request(self, request: Message, expected_types: Sequence[Type[Message]]) -> Message:
        if not self._started.is_set():
            raise CTraderServiceError("cTrader gateway is not started.")
        if not self._connected.is_set():
            raise CTraderServiceError("cTrader gateway is not connected.")

        response_event = threading.Event()
        outcome: dict[str, Any] = {}

        def _send() -> None:
            deferred = self.client.send(request)

            def _on_success(message: Message) -> None:
                payload = Protobuf.extract(message)
                if isinstance(payload, ProtoOAErrorRes):
                    outcome["error"] = CTraderApiError(payload.errorCode, payload.description)
                elif not isinstance(payload, tuple(expected_types)):
                    expected = ",".join(t.__name__ for t in expected_types)
                    outcome["error"] = CTraderServiceError(
                        f"Unexpected response type {type(payload).__name__}, expected one of {expected}"
                    )
                else:
                    outcome["response"] = payload
                response_event.set()

            def _on_error(failure) -> None:
                outcome["error"] = CTraderServiceError(str(failure))
                response_event.set()

            deferred.addCallbacks(_on_success, _on_error)

        reactor.callFromThread(_send)

        if not response_event.wait(timeout=self.settings.ctrader_request_timeout_seconds):
            raise CTraderTimeoutError(f"Timed out while waiting for {type(request).__name__}.")
        if "error" in outcome:
            raise outcome["error"]
        return outcome["response"]

    def _run_in_reactor(self, fn) -> None:
        finished = threading.Event()
        failure: dict[str, Exception] = {}

        def _run() -> None:
            try:
                fn()
            except Exception as exc:  # pragma: no cover - defensive
                failure["exc"] = exc
            finally:
                finished.set()

        reactor.callFromThread(_run)
        finished.wait(timeout=self.settings.ctrader_request_timeout_seconds)
        if "exc" in failure:
            raise failure["exc"]

    def _on_connected(self, _client: Client) -> None:
        self._connected.set()

    def _on_disconnected(self, _client: Client, reason) -> None:
        if not self._connected.is_set():
            self._connection_error = CTraderServiceError(f"Disconnected before connection completed: {reason}")
            self._connected.set()
