from decimal import Decimal, ROUND_DOWN

from google.protobuf.json_format import MessageToDict

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetAccountListByAccessTokenRes,
    ProtoOATraderReq,
    ProtoOATraderRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATradeSide

from app.core.config import Settings
from app.services.ctrader.history import CTraderHistoryClient
from app.services.ctrader.models import CTraderAccount, CTraderSymbol
from app.services.ctrader.orders import CTraderOrderClient
from app.services.ctrader.symbols import CTraderSymbolClient
from app.services.ctrader.transport import CTraderTransport
from app.services.exceptions import CTraderApiError, CTraderServiceError


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

    def ensure_account_authorized(self, account_id: int) -> None:
        self._transport.ensure_account_authorized(account_id)

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

    def close_positions(
        self,
        account_id: int,
        tickets: list[int] | None = None,
    ) -> tuple[list[int], list[dict], list[dict], list[int]]:
        open_positions = self._orders.get_open_positions(account_id)
        requested_tickets = set(tickets) if tickets is not None else None
        selected_positions = (
            [p for p in open_positions if p["position_id"] in requested_tickets]
            if requested_tickets is not None
            else open_positions
        )
        open_ticket_set = {position["position_id"] for position in open_positions}
        not_found_tickets = (
            sorted(ticket for ticket in requested_tickets if ticket not in open_ticket_set)
            if requested_tickets is not None
            else []
        )

        closed_tickets: list[int] = []
        executions: list[dict] = []
        skipped_tickets: list[dict] = []
        for position in selected_positions:
            position_id = position["position_id"]
            volume = position["volume"]
            try:
                execution = self._orders.close_position(account_id, position_id, volume)
                closed_tickets.append(position_id)
                executions.append(execution)
            except CTraderApiError as exc:
                skipped_tickets.append(
                    {
                        "ticket": position_id,
                        "code": exc.code,
                        "description": exc.description,
                    }
                )

        return closed_tickets, executions, skipped_tickets, not_found_tickets

    def close_positions_by_symbol(
        self,
        account_id: int,
        symbol_id: int,
        directions: list[str],
    ) -> tuple[list[int], list[dict], list[dict]]:
        open_positions = self._orders.get_open_positions(account_id)
        requested = {direction.upper() for direction in directions}
        close_buy = "ALL" in requested or "LONG" in requested
        close_sell = "ALL" in requested or "SHORT" in requested

        selected_positions = []
        for position in open_positions:
            if position["symbol_id"] != symbol_id:
                continue
            is_buy = position["trade_side"] == ProtoOATradeSide.Value("BUY")
            is_sell = position["trade_side"] == ProtoOATradeSide.Value("SELL")
            if (is_buy and close_buy) or (is_sell and close_sell):
                selected_positions.append(position)

        closed_tickets: list[int] = []
        executions: list[dict] = []
        skipped_tickets: list[dict] = []
        for position in selected_positions:
            position_id = position["position_id"]
            try:
                execution = self._orders.close_position(account_id, position_id, position["volume"])
                closed_tickets.append(position_id)
                executions.append(execution)
            except CTraderApiError as exc:
                skipped_tickets.append(
                    {
                        "ticket": position_id,
                        "code": exc.code,
                        "description": exc.description,
                    }
                )

        return closed_tickets, executions, skipped_tickets

    def amend_position_take_profit(
        self,
        account_id: int,
        position_id: int,
        take_profit: float | None,
    ) -> dict:
        position = self._find_open_position(account_id, position_id)
        if position is None:
            raise CTraderServiceError(f"Position {position_id} is not currently open.")
        if take_profit is None:
            # Omit takeProfit to clear it while preserving existing stopLoss.
            if position["has_stop_loss"]:
                return self._orders.amend_position_sltp(
                    account_id,
                    position_id,
                    stop_loss=position["stop_loss"],
                )
            return {"status": "no_change", "reason": "take_profit_already_unset"}
        if position["has_stop_loss"]:
            return self._orders.amend_position_sltp(
                account_id,
                position_id,
                stop_loss=position["stop_loss"],
                take_profit=take_profit,
            )
        return self._orders.amend_position_sltp(account_id, position_id, take_profit=take_profit)

    def remove_take_profit_all_positions(
        self,
        account_id: int,
    ) -> tuple[list[int], list[dict], list[dict]]:
        open_positions = self._orders.get_open_positions(account_id)

        updated_tickets: list[int] = []
        executions: list[dict] = []
        skipped_tickets: list[dict] = []
        for position in open_positions:
            position_id = position["position_id"]
            try:
                if not position["has_take_profit"]:
                    continue
                if position["has_stop_loss"]:
                    execution = self._orders.amend_position_sltp(
                        account_id,
                        position_id,
                        stop_loss=position["stop_loss"],
                    )
                else:
                    execution = self._orders.amend_position_sltp(account_id, position_id)
                updated_tickets.append(position_id)
                executions.append(execution)
            except CTraderApiError as exc:
                skipped_tickets.append(
                    {
                        "ticket": position_id,
                        "code": exc.code,
                        "description": exc.description,
                    }
                )

        return updated_tickets, executions, skipped_tickets

    def amend_position_stop_loss(
        self,
        account_id: int,
        position_id: int,
        stop_loss: float | None,
    ) -> dict:
        position = self._find_open_position(account_id, position_id)
        if position is None:
            raise CTraderServiceError(f"Position {position_id} is not currently open.")
        if stop_loss is None:
            # Omit stopLoss to clear it while preserving existing takeProfit.
            if position["has_take_profit"]:
                return self._orders.amend_position_sltp(
                    account_id,
                    position_id,
                    take_profit=position["take_profit"],
                )
            return {"status": "no_change", "reason": "stop_loss_already_unset"}
        if position["has_take_profit"]:
            return self._orders.amend_position_sltp(
                account_id,
                position_id,
                stop_loss=stop_loss,
                take_profit=position["take_profit"],
            )
        return self._orders.amend_position_sltp(account_id, position_id, stop_loss=stop_loss)

    def remove_stop_loss_all_positions(
        self,
        account_id: int,
    ) -> tuple[list[int], list[dict], list[dict]]:
        open_positions = self._orders.get_open_positions(account_id)

        updated_tickets: list[int] = []
        executions: list[dict] = []
        skipped_tickets: list[dict] = []
        for position in open_positions:
            position_id = position["position_id"]
            try:
                if not position["has_stop_loss"]:
                    continue
                if position["has_take_profit"]:
                    execution = self._orders.amend_position_sltp(
                        account_id,
                        position_id,
                        take_profit=position["take_profit"],
                    )
                else:
                    execution = self._orders.amend_position_sltp(account_id, position_id)
                updated_tickets.append(position_id)
                executions.append(execution)
            except CTraderApiError as exc:
                skipped_tickets.append(
                    {
                        "ticket": position_id,
                        "code": exc.code,
                        "description": exc.description,
                    }
                )

        return updated_tickets, executions, skipped_tickets

    def _find_open_position(self, account_id: int, position_id: int) -> dict | None:
        for position in self._orders.get_open_positions(account_id):
            if position["position_id"] == position_id:
                return position
        return None
