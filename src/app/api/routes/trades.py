from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_gateway
from app.core.config import get_settings
from app.schemas.trades import PlaceTradeRequest, PlaceTradeResponse
from app.services.ctrader_gateway import CTraderGateway

router = APIRouter(prefix="/trade", tags=["trade"])


def _execute_trade(
    payload: PlaceTradeRequest,
) -> PlaceTradeResponse:
    gateway = get_gateway()
    settings = get_settings()
    symbol_id, resolved_symbol_name = gateway.resolve_symbol_id(
        settings.ctrader_account_id,
        payload.symbol_name,
    )
    symbol = gateway.get_symbol_details(settings.ctrader_account_id, symbol_id)
    volume_units = gateway.lots_to_volume_units(symbol, payload.volume_lots)

    execution = gateway.place_market_order(
        account_id=settings.ctrader_account_id,
        symbol_id=symbol_id,
        side=payload.side,
        volume=volume_units,
        label=payload.label,
        comment=payload.comment,
    )
    return PlaceTradeResponse(
        account_id=settings.ctrader_account_id,
        symbol_id=symbol_id,
        symbol_name=resolved_symbol_name,
        volume_lots=payload.volume_lots,
        volume_units=volume_units,
        execution=execution,
    )


@router.post("", response_model=PlaceTradeResponse)
def place_trade(
    payload: PlaceTradeRequest,
    _gateway: CTraderGateway = Depends(get_gateway),
) -> PlaceTradeResponse:
    return _execute_trade(payload)


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
    _gateway: CTraderGateway = Depends(get_gateway),
) -> list[dict]:
    if (from_date is None) != (to_date is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both 'from' and 'to' dates, or omit both for last 30 days.",
        )

    if from_date is None and to_date is None:
        to_date = datetime.now(tz=UTC).date()
        from_date = to_date - timedelta(days=29)

    if from_date > to_date:
        raise HTTPException(status_code=400, detail="'from' date cannot be after 'to' date.")

    settings = get_settings()
    gateway = get_gateway()
    return gateway.get_deal_history(settings.ctrader_account_id, from_date, to_date)
