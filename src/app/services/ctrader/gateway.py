from decimal import Decimal, ROUND_DOWN

from google.protobuf.json_format import MessageToDict

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
    ProtoOATraderReq,
    ProtoOATraderRes,
)

from app.core.config import Settings
from app.services.ctrader.history import CTraderHistoryClient
from app.services.ctrader.models import CTraderAccount, CTraderSymbol
from app.services.ctrader.orders import CTraderOrderClient
from app.services.ctrader.symbols import CTraderSymbolClient
from app.services.ctrader.transport import CTraderTransport
from app.services.exceptions import CTraderServiceError


class CTraderGateway:
    """Facade over cTrader Open API domain clients."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._transport = CTraderTransport(settings)
        self._symbols = CTraderSymbolClient(self._transport)
        self._orders = CTraderOrderClient(self._transport)
        self._history = CTraderHistoryClient(self._transport, self._symbols)

    def start(self) -> None:
        self._transport.start()
        self._transport.authenticate()

    def stop(self) -> None:
        self._transport.stop()

    def get_accounts(self) -> list[CTraderAccount]:
        req = ProtoOAGetAccountListByAccessTokenReq()
        req.accessToken = self._settings.ctrader_access_token
        response = self._transport.request(req, expected_types=(ProtoOAGetAccountListByAccessTokenRes,))
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

    def get_trader_info(self, account_id: int) -> dict:
        req = ProtoOATraderReq()
        req.ctidTraderAccountId = account_id
        response = self._transport.request(req, expected_types=(ProtoOATraderRes,))
        return MessageToDict(response.trader, preserving_proto_field_name=True)

    def resolve_symbol_id(self, account_id: int, symbol_name: str) -> tuple[int, str]:
        return self._symbols.resolve_symbol_id(account_id, symbol_name)

    def get_symbol_details(self, account_id: int, symbol_id: int) -> CTraderSymbol:
        return self._symbols.get_symbol_details(account_id, symbol_id)

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

    def place_market_order(
        self,
        account_id: int,
        symbol_id: int,
        side: str,
        volume: int,
        label: str | None = None,
        comment: str | None = None,
    ) -> dict:
        return self._orders.place_market_order(account_id, symbol_id, side, volume, label, comment)

    def get_deal_history(
        self,
        account_id: int,
        from_date,
        to_date,
        max_rows: int = 5000,
    ) -> list[dict]:
        return self._history.get_deal_history(account_id, from_date, to_date, max_rows)
