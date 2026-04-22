from datetime import date
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_trade_history_service, get_trade_service
from app.schemas.trades import (
    CloseAllTradesResponse,
    CloseAllTradesRequest,
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
from app.services.trade_history_service import TradeHistoryService
from app.services.trade_service import TradeService

router = APIRouter(prefix="/trade", tags=["trade"])


@router.post("", response_model=PlaceTradeResponse)
def place_trade(
    payload: PlaceTradeRequest,
    service: TradeService = Depends(get_trade_service),
) -> PlaceTradeResponse:
    return service.place_trade(payload)


@router.post("/close-all", response_model=CloseAllTradesResponse)
def close_all_trades(
    payload: CloseAllTradesRequest,
    service: TradeService = Depends(get_trade_service),
) -> CloseAllTradesResponse:
    return service.close_all_trades(payload)


@router.post("/close-by-ticket", response_model=CloseByTicketResponse)
def close_trades_by_ticket(
    payload: CloseByTicketRequest,
    service: TradeService = Depends(get_trade_service),
) -> CloseByTicketResponse:
    return service.close_trades_by_ticket(payload)


@router.post("/close-by-symbol", response_model=CloseBySymbolResponse)
def close_trades_by_symbol(
    payload: CloseBySymbolRequest,
    service: TradeService = Depends(get_trade_service),
) -> CloseBySymbolResponse:
    return service.close_trades_by_symbol(payload)


@router.get("/all-trades", response_model=list[dict])
def get_all_trades(
    signal_type: str = Query(..., min_length=1, description="Signal type mapped to cTrader account ID."),
    from_date: date | None = Query(
        None,
        alias="from",
        description="Start date filter (YYYY-MM-DD, inclusive)",
    ),
    to_date: date | None = Query(
        None,
        alias="to",
        description="End date filter (YYYY-MM-DD, inclusive)",
    ),
    service: TradeHistoryService = Depends(get_trade_history_service),
) -> list[dict]:
    return service.get_all_trades(signal_type, from_date, to_date)


@router.post("/set-take-profit", response_model=TakeProfitResponse)
def set_take_profit(
    payload: SetTakeProfitRequest,
    service: TradeService = Depends(get_trade_service),
) -> TakeProfitResponse:
    return service.set_take_profit(payload)


@router.post("/remove-take-profit", response_model=TakeProfitResponse)
def remove_take_profit(
    payload: RemoveTakeProfitRequest,
    service: TradeService = Depends(get_trade_service),
) -> TakeProfitResponse:
    return service.remove_take_profit(payload)


@router.post("/remove-all-take-profit", response_model=RemoveAllTakeProfitResponse)
def remove_all_take_profit(
    payload: RemoveAllTakeProfitRequest,
    service: TradeService = Depends(get_trade_service),
) -> RemoveAllTakeProfitResponse:
    return service.remove_all_take_profit(payload)


@router.post("/set-stop-loss", response_model=StopLossResponse)
def set_stop_loss(
    payload: SetStopLossRequest,
    service: TradeService = Depends(get_trade_service),
) -> StopLossResponse:
    return service.set_stop_loss(payload)


@router.post("/remove-stop-loss", response_model=StopLossResponse)
def remove_stop_loss(
    payload: RemoveStopLossRequest,
    service: TradeService = Depends(get_trade_service),
) -> StopLossResponse:
    return service.remove_stop_loss(payload)


@router.post("/remove-all-stop-loss", response_model=RemoveAllStopLossResponse)
def remove_all_stop_loss(
    payload: RemoveAllStopLossRequest,
    service: TradeService = Depends(get_trade_service),
) -> RemoveAllStopLossResponse:
    return service.remove_all_stop_loss(payload)
