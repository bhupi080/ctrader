from fastapi import APIRouter, Depends

from app.api.dependencies import get_gateway
from app.core.config import get_settings
from app.schemas.trades import PlaceTradeRequest, PlaceTradeResponse
from app.services.ctrader_gateway import CTraderGateway

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=PlaceTradeResponse)
def place_trade(
    payload: PlaceTradeRequest,
    gateway: CTraderGateway = Depends(get_gateway),
) -> PlaceTradeResponse:
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
