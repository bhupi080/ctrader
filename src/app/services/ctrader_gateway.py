import threading
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any, Sequence, Type

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from twisted.internet import reactor

from ctrader_open_api import Client, EndPoints, Protobuf, TcpProtocol
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthReq,
    ProtoOAAccountAuthRes,
    ProtoOAApplicationAuthReq,
    ProtoOAApplicationAuthRes,
    ProtoOAErrorRes,
    ProtoOAExecutionEvent,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
    ProtoOANewOrderReq,
    ProtoOAOrderErrorEvent,
    ProtoOASymbolByIdReq,
    ProtoOASymbolByIdRes,
    ProtoOASymbolsListReq,
    ProtoOASymbolsListRes,
    ProtoOATraderReq,
    ProtoOATraderRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOAOrderType, ProtoOATradeSide

from app.core.config import Settings
from app.services.exceptions import CTraderApiError, CTraderServiceError, CTraderTimeoutError


@dataclass
class CTraderAccount:
    account_id: int
    is_live: bool
    trader_login: str | None


@dataclass
class CTraderSymbol:
    symbol_id: int
    symbol_name: str
    lot_size: int
    step_volume: int
    min_volume: int
    max_volume: int


class CTraderGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        host_type = settings.ctrader_host.lower()
        host = EndPoints.PROTOBUF_LIVE_HOST if host_type == "live" else EndPoints.PROTOBUF_DEMO_HOST

        self._client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self._connected = threading.Event()
        self._started = threading.Event()
        self._connection_error: Exception | None = None

        self._client.setConnectedCallback(self._on_connected)
        self._client.setDisconnectedCallback(self._on_disconnected)

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

        self._run_in_reactor(self._client.startService)
        self._started.set()

        if not self._connected.wait(timeout=self._settings.ctrader_request_timeout_seconds):
            raise CTraderTimeoutError("Timed out while connecting to cTrader.")
        if self._connection_error:
            raise CTraderServiceError(str(self._connection_error))

        self._authenticate()

    def stop(self) -> None:
        if not self._started.is_set():
            return
        self._run_in_reactor(self._client.stopService)
        if reactor.running:
            reactor.callFromThread(reactor.stop)

    def get_accounts(self) -> list[CTraderAccount]:
        response = self._request(
            self._build_account_list_req(),
            expected_types=(ProtoOAGetAccountListByAccessTokenRes,),
        )
        accounts: list[CTraderAccount] = []
        for account in response.ctidTraderAccount:
            accounts.append(
                CTraderAccount(
                    account_id=account.ctidTraderAccountId,
                    is_live=account.isLive,
                    trader_login=str(account.traderLogin) if account.traderLogin else None,
                )
            )
        return accounts

    def get_trader_info(self, account_id: int) -> dict[str, Any]:
        req = ProtoOATraderReq()
        req.ctidTraderAccountId = account_id
        response = self._request(req, expected_types=(ProtoOATraderRes,))
        return MessageToDict(response.trader, preserving_proto_field_name=True)

    def place_market_order(
        self,
        account_id: int,
        symbol_id: int,
        side: str,
        volume: int,
        label: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        req = ProtoOANewOrderReq()
        req.ctidTraderAccountId = account_id
        req.symbolId = symbol_id
        req.orderType = ProtoOAOrderType.Value("MARKET")
        req.tradeSide = ProtoOATradeSide.Value(side.upper())
        req.volume = volume
        if label:
            req.label = label
        if comment:
            req.comment = comment

        response = self._request(
            req,
            expected_types=(ProtoOAExecutionEvent, ProtoOAOrderErrorEvent),
        )
        if isinstance(response, ProtoOAOrderErrorEvent):
            raise CTraderApiError(response.errorCode, response.description or "Order rejected.")
        return MessageToDict(response, preserving_proto_field_name=True)

    def resolve_symbol_id(self, account_id: int, symbol_name: str) -> tuple[int, str]:
        req = ProtoOASymbolsListReq()
        req.ctidTraderAccountId = account_id
        req.includeArchivedSymbols = False
        response = self._request(req, expected_types=(ProtoOASymbolsListRes,))

        target = symbol_name.strip().upper()
        for symbol in response.symbol:
            if symbol.symbolName.upper() == target:
                return symbol.symbolId, symbol.symbolName
        raise CTraderServiceError(f"Symbol '{symbol_name}' not found for account {account_id}.")

    def get_symbol_details(self, account_id: int, symbol_id: int) -> CTraderSymbol:
        req = ProtoOASymbolByIdReq()
        req.ctidTraderAccountId = account_id
        req.symbolId.append(symbol_id)
        response = self._request(req, expected_types=(ProtoOASymbolByIdRes,))
        if not response.symbol:
            raise CTraderServiceError(f"Symbol id '{symbol_id}' not found for account {account_id}.")
        symbol = response.symbol[0]
        return CTraderSymbol(
            symbol_id=symbol.symbolId,
            symbol_name="",
            lot_size=symbol.lotSize,
            step_volume=symbol.stepVolume,
            min_volume=symbol.minVolume,
            max_volume=symbol.maxVolume,
        )

    def lots_to_volume_units(self, symbol: CTraderSymbol, volume_lots: float) -> int:
        lots = Decimal(str(volume_lots))
        raw_units = int((lots * Decimal(symbol.lot_size)).quantize(Decimal("1"), rounding=ROUND_DOWN))
        if raw_units <= 0:
            raise CTraderServiceError("volume_lots is too small for this symbol lot size.")

        if symbol.step_volume > 0 and raw_units % symbol.step_volume != 0:
            raise CTraderServiceError(
                f"Calculated volume units={raw_units} is not aligned to stepVolume={symbol.step_volume}."
            )

        if raw_units < symbol.min_volume:
            raise CTraderServiceError(
                f"Calculated volume units={raw_units} is below minVolume={symbol.min_volume}."
            )
        if symbol.max_volume > 0 and raw_units > symbol.max_volume:
            raise CTraderServiceError(
                f"Calculated volume units={raw_units} is above maxVolume={symbol.max_volume}."
            )
        return raw_units

    def _authenticate(self) -> None:
        app_req = ProtoOAApplicationAuthReq()
        app_req.clientId = self._settings.ctrader_client_id
        app_req.clientSecret = self._settings.ctrader_client_secret
        self._request(app_req, expected_types=(ProtoOAApplicationAuthRes,))

        account_req = ProtoOAAccountAuthReq()
        account_req.ctidTraderAccountId = self._settings.ctrader_account_id
        account_req.accessToken = self._settings.ctrader_access_token
        self._request(account_req, expected_types=(ProtoOAAccountAuthRes,))

    def _build_account_list_req(self) -> ProtoOAGetAccountListByAccessTokenReq:
        req = ProtoOAGetAccountListByAccessTokenReq()
        req.accessToken = self._settings.ctrader_access_token
        return req

    def _request(self, request: Message, expected_types: Sequence[Type[Message]]) -> Message:
        if not self._started.is_set():
            raise CTraderServiceError("cTrader gateway is not started.")
        if not self._connected.is_set():
            raise CTraderServiceError("cTrader gateway is not connected.")

        response_event = threading.Event()
        outcome: dict[str, Any] = {}

        def _send() -> None:
            deferred = self._client.send(request)

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

        if not response_event.wait(timeout=self._settings.ctrader_request_timeout_seconds):
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
        finished.wait(timeout=self._settings.ctrader_request_timeout_seconds)
        if "exc" in failure:
            raise failure["exc"]

    def _on_connected(self, _client: Client) -> None:
        self._connected.set()

    def _on_disconnected(self, _client: Client, reason) -> None:
        if not self._connected.is_set():
            self._connection_error = CTraderServiceError(f"Disconnected before connection completed: {reason}")
            self._connected.set()

