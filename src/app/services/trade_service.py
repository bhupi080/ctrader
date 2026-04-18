from app.core.config import Settings
from app.schemas.trades import (
    CloseAllTradesResponse,
    CloseBySymbolRequest,
    CloseBySymbolResponse,
    CloseByTicketRequest,
    CloseByTicketResponse,
    PlaceTradeRequest,
    PlaceTradeResponse,
    RemoveAllTakeProfitResponse,
    SetTakeProfitRequest,
    TakeProfitResponse,
)
from app.services.ctrader import CTraderGateway


class TradeService:
    def __init__(self, gateway: CTraderGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._settings = settings

    def place_trade(self, payload: PlaceTradeRequest) -> PlaceTradeResponse:
        symbol_id, resolved_symbol_name = self._gateway.resolve_symbol_id(
            self._settings.ctrader_account_id,
            payload.symbol_name,
        )
        symbol = self._gateway.get_symbol_details(self._settings.ctrader_account_id, symbol_id)
        volume_units = self._gateway.lots_to_volume_units(symbol, payload.volume_lots)

        execution = self._gateway.place_market_order(
            account_id=self._settings.ctrader_account_id,
            symbol_id=symbol_id,
            side=payload.side,
            volume=volume_units,
            label=payload.label,
            comment=payload.comment,
        )
        return PlaceTradeResponse(
            account_id=self._settings.ctrader_account_id,
            symbol_id=symbol_id,
            symbol_name=resolved_symbol_name,
            volume_lots=payload.volume_lots,
            volume_units=volume_units,
            execution=execution,
        )

    def close_all_trades(self) -> CloseAllTradesResponse:
        closed_tickets, executions, skipped_tickets, not_found_tickets = self._gateway.close_positions(
            self._settings.ctrader_account_id
        )
        return CloseAllTradesResponse(
            account_id=self._settings.ctrader_account_id,
            closed_tickets=closed_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
            not_found_tickets=not_found_tickets,
        )

    def close_trades_by_ticket(self, payload: CloseByTicketRequest) -> CloseByTicketResponse:
        closed_tickets, executions, skipped_tickets, not_found_tickets = self._gateway.close_positions(
            self._settings.ctrader_account_id,
            tickets=payload.tickets,
        )
        return CloseByTicketResponse(
            account_id=self._settings.ctrader_account_id,
            requested_tickets=payload.tickets,
            closed_tickets=closed_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
            not_found_tickets=not_found_tickets,
        )

    def close_trades_by_symbol(self, payload: CloseBySymbolRequest) -> CloseBySymbolResponse:
        symbol_id, resolved_symbol_name = self._gateway.resolve_symbol_id(
            self._settings.ctrader_account_id,
            payload.symbol_name,
        )
        closed_tickets, executions, skipped_tickets = self._gateway.close_positions_by_symbol(
            self._settings.ctrader_account_id,
            symbol_id=symbol_id,
            directions=[payload.direction],
        )
        return CloseBySymbolResponse(
            account_id=self._settings.ctrader_account_id,
            symbol_id=symbol_id,
            symbol_name=resolved_symbol_name,
            requested_direction=payload.direction,
            closed_tickets=closed_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
            not_found_tickets=[],
        )

    def set_take_profit(self, payload: SetTakeProfitRequest) -> TakeProfitResponse:
        execution = self._gateway.amend_position_take_profit(
            account_id=self._settings.ctrader_account_id,
            position_id=payload.ticket,
            take_profit=payload.take_profit,
        )
        return TakeProfitResponse(
            account_id=self._settings.ctrader_account_id,
            ticket=payload.ticket,
            execution=execution,
        )

    def remove_take_profit(self, ticket: int) -> TakeProfitResponse:
        execution = self._gateway.amend_position_take_profit(
            account_id=self._settings.ctrader_account_id,
            position_id=ticket,
            take_profit=None,
        )
        return TakeProfitResponse(
            account_id=self._settings.ctrader_account_id,
            ticket=ticket,
            execution=execution,
        )

    def remove_all_take_profit(self) -> RemoveAllTakeProfitResponse:
        updated_tickets, executions, skipped_tickets = self._gateway.remove_take_profit_all_positions(
            self._settings.ctrader_account_id
        )
        return RemoveAllTakeProfitResponse(
            account_id=self._settings.ctrader_account_id,
            updated_tickets=updated_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
        )
