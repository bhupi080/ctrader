from fastapi import HTTPException

from app.schemas.trades import (
    CloseAllTradesRequest,
    CloseAllTradesResponse,
    CloseBySymbolRequest,
    CloseBySymbolResponse,
    CloseByTicketRequest,
    CloseByTicketResponse,
    PlaceTradeRequest,
    PlaceTradeResponse,
    RemoveAllTakeProfitRequest,
    RemoveAllTakeProfitResponse,
    RemoveAllStopLossRequest,
    RemoveAllStopLossResponse,
    RemoveTakeProfitRequest,
    RemoveStopLossRequest,
    SetTakeProfitRequest,
    SetStopLossRequest,
    StopLossResponse,
    TakeProfitResponse,
)
from app.services.ctrader import CTraderGateway
from app.services.signal_account_map import SignalAccountMap, SignalAccountMapError
from app.services.symbol_mapping import SymbolMapping


class TradeService:
    def __init__(
        self,
        gateway: CTraderGateway,
        signal_account_map: SignalAccountMap,
        symbol_mapping: SymbolMapping,
        fxpro_symbol_mapping_enabled: bool,
    ) -> None:
        self._gateway = gateway
        self._signal_account_map = signal_account_map
        self._symbol_mapping = symbol_mapping
        self._fxpro_symbol_mapping_enabled = fxpro_symbol_mapping_enabled

    def place_trade(self, payload: PlaceTradeRequest) -> PlaceTradeResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        symbol_name = self._map_symbol_if_enabled(payload.symbol_name)
        symbol_id, resolved_symbol_name = self._gateway.resolve_symbol_id(
            account_id,
            symbol_name,
        )
        symbol = self._gateway.get_symbol_details(account_id, symbol_id)
        volume_units = self._gateway.lots_to_volume_units(symbol, payload.volume_lots)

        execution = self._gateway.place_market_order(
            account_id=account_id,
            symbol_id=symbol_id,
            side=payload.side,
            volume=volume_units,
            label=payload.label,
            comment=payload.comment,
        )
        return PlaceTradeResponse(
            account_id=account_id,
            symbol_id=symbol_id,
            symbol_name=resolved_symbol_name,
            volume_lots=payload.volume_lots,
            volume_units=volume_units,
            execution=execution,
        )

    def close_all_trades(self, payload: CloseAllTradesRequest) -> CloseAllTradesResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        closed_tickets, executions, skipped_tickets, not_found_tickets = self._gateway.close_positions(
            account_id
        )
        return CloseAllTradesResponse(
            account_id=account_id,
            closed_tickets=closed_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
            not_found_tickets=not_found_tickets,
        )

    def close_trades_by_ticket(self, payload: CloseByTicketRequest) -> CloseByTicketResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        closed_tickets, executions, skipped_tickets, not_found_tickets = self._gateway.close_positions(
            account_id,
            tickets=payload.tickets,
        )
        return CloseByTicketResponse(
            account_id=account_id,
            requested_tickets=payload.tickets,
            closed_tickets=closed_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
            not_found_tickets=not_found_tickets,
        )

    def close_trades_by_symbol(self, payload: CloseBySymbolRequest) -> CloseBySymbolResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        symbol_name = self._map_symbol_if_enabled(payload.symbol_name)
        symbol_id, resolved_symbol_name = self._gateway.resolve_symbol_id(
            account_id,
            symbol_name,
        )
        closed_tickets, executions, skipped_tickets = self._gateway.close_positions_by_symbol(
            account_id,
            symbol_id=symbol_id,
            directions=[payload.direction],
        )
        return CloseBySymbolResponse(
            account_id=account_id,
            symbol_id=symbol_id,
            symbol_name=resolved_symbol_name,
            requested_direction=payload.direction,
            closed_tickets=closed_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
            not_found_tickets=[],
        )

    def set_take_profit(self, payload: SetTakeProfitRequest) -> TakeProfitResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        execution = self._gateway.amend_position_take_profit(
            account_id=account_id,
            position_id=payload.ticket,
            take_profit=payload.take_profit,
        )
        return TakeProfitResponse(
            account_id=account_id,
            ticket=payload.ticket,
            execution=execution,
        )

    def remove_take_profit(self, payload: RemoveTakeProfitRequest) -> TakeProfitResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        execution = self._gateway.amend_position_take_profit(
            account_id=account_id,
            position_id=payload.ticket,
            take_profit=None,
        )
        return TakeProfitResponse(
            account_id=account_id,
            ticket=payload.ticket,
            execution=execution,
        )

    def remove_all_take_profit(self, payload: RemoveAllTakeProfitRequest) -> RemoveAllTakeProfitResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        updated_tickets, executions, skipped_tickets = self._gateway.remove_take_profit_all_positions(
            account_id
        )
        return RemoveAllTakeProfitResponse(
            account_id=account_id,
            updated_tickets=updated_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
        )

    def set_stop_loss(self, payload: SetStopLossRequest) -> StopLossResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        execution = self._gateway.amend_position_stop_loss(
            account_id=account_id,
            position_id=payload.ticket,
            stop_loss=payload.stop_loss,
        )
        return StopLossResponse(
            account_id=account_id,
            ticket=payload.ticket,
            execution=execution,
        )

    def remove_stop_loss(self, payload: RemoveStopLossRequest) -> StopLossResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        execution = self._gateway.amend_position_stop_loss(
            account_id=account_id,
            position_id=payload.ticket,
            stop_loss=None,
        )
        return StopLossResponse(
            account_id=account_id,
            ticket=payload.ticket,
            execution=execution,
        )

    def remove_all_stop_loss(self, payload: RemoveAllStopLossRequest) -> RemoveAllStopLossResponse:
        account_id = self._resolve_account_id(payload.signal_type)
        updated_tickets, executions, skipped_tickets = self._gateway.remove_stop_loss_all_positions(
            account_id
        )
        return RemoveAllStopLossResponse(
            account_id=account_id,
            updated_tickets=updated_tickets,
            executions=executions,
            skipped_tickets=skipped_tickets,
        )

    def _resolve_account_id(self, signal_type: str) -> int:
        try:
            account_id = self._signal_account_map.resolve_account_id(signal_type)
        except SignalAccountMapError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        self._gateway.ensure_account_authorized(account_id)
        return account_id

    def _map_symbol_if_enabled(self, symbol_name: str) -> str:
        if not self._fxpro_symbol_mapping_enabled:
            return symbol_name
        return self._symbol_mapping.map_symbol(symbol_name)
