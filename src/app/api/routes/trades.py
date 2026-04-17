from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_trade_history_service, get_trade_service
from app.schemas.trades import PlaceTradeRequest, PlaceTradeResponse
from app.services.trade_history_service import TradeHistoryService
from app.services.trade_service import TradeService

router = APIRouter(prefix="/trade", tags=["trade"])


@router.post("", response_model=PlaceTradeResponse)
def place_trade(
    payload: PlaceTradeRequest,
    service: TradeService = Depends(get_trade_service),
) -> PlaceTradeResponse:
    return service.place_trade(payload)


@router.get("/all-trades", response_model=list[dict])
def get_all_trades(
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
    return service.get_all_trades(from_date, to_date)
