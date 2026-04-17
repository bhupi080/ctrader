import os

from dotenv import load_dotenv
from twisted.internet import reactor

from ctrader_open_api import Client, EndPoints, Protobuf, TcpProtocol
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthReq,
    ProtoOAAccountAuthRes,
    ProtoOAApplicationAuthReq,
    ProtoOAApplicationAuthRes,
    ProtoOAErrorRes,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def main() -> None:
    load_dotenv()

    client_id = _require_env("CTRADER_CLIENT_ID")
    client_secret = _require_env("CTRADER_CLIENT_SECRET")
    account_id = int(_require_env("CTRADER_ACCOUNT_ID"))
    access_token = _require_env("CTRADER_ACCESS_TOKEN")
    host_type = os.getenv("CTRADER_HOST", "demo").strip().lower()

    host = (
        EndPoints.PROTOBUF_LIVE_HOST
        if host_type == "live"
        else EndPoints.PROTOBUF_DEMO_HOST
    )

    client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)

    state = {"exit_code": 0, "intentional_shutdown": False}

    def shutdown(code: int = 0) -> None:
        state["exit_code"] = code
        state["intentional_shutdown"] = True
        client.stopService()
        if reactor.running:
            reactor.callLater(0.1, reactor.stop)

    def on_error(failure) -> None:
        print(f"Request failed: {failure}")
        shutdown(1)

    def on_message_received(_client, message) -> None:
        payload = Protobuf.extract(message)
        if isinstance(payload, ProtoOAErrorRes):
            print(f"API error: code={payload.errorCode} description={payload.description}")
            shutdown(1)
        elif isinstance(payload, ProtoOAApplicationAuthRes):
            print("Application auth succeeded.")
        elif isinstance(payload, ProtoOAGetAccountListByAccessTokenRes):
            accounts = list(payload.ctidTraderAccount)
            if not accounts:
                print("No trading accounts are linked to this access token.")
                shutdown(1)
                return

            available_ids = [acct.ctidTraderAccountId for acct in accounts]
            print(f"Accounts in token scope: {available_ids}")
            if account_id not in available_ids:
                print(
                    f"Configured CTRADER_ACCOUNT_ID={account_id} is not in token scope. "
                    "Update .env with one of the listed IDs."
                )
                shutdown(1)
                return

            account_req = ProtoOAAccountAuthReq()
            account_req.ctidTraderAccountId = account_id
            account_req.accessToken = access_token
            account_deferred = client.send(account_req)
            account_deferred.addErrback(on_error)
        elif isinstance(payload, ProtoOAAccountAuthRes):
            print(f"Account auth succeeded for account {account_id}.")
            shutdown(0)

    def on_disconnected(_client, reason) -> None:
        if not state["intentional_shutdown"]:
            print(f"Disconnected unexpectedly: {reason}")

    def on_connected(_client) -> None:
        print(f"Connected to cTrader {host_type} endpoint.")

        app_req = ProtoOAApplicationAuthReq()
        app_req.clientId = client_id
        app_req.clientSecret = client_secret
        app_deferred = client.send(app_req)

        def after_app_auth(_):
            account_list_req = ProtoOAGetAccountListByAccessTokenReq()
            account_list_req.accessToken = access_token
            return client.send(account_list_req)

        app_deferred.addCallback(after_app_auth)
        app_deferred.addErrback(on_error)

    client.setConnectedCallback(on_connected)
    client.setDisconnectedCallback(on_disconnected)
    client.setMessageReceivedCallback(on_message_received)

    client.startService()
    reactor.run()
    raise SystemExit(state["exit_code"])


if __name__ == "__main__":
    main()
