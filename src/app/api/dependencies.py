from fastapi import HTTPException, status

from app.core import state
from app.services.ctrader_gateway import CTraderGateway


def get_gateway() -> CTraderGateway:
    if state.gateway is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="cTrader gateway is not initialized.",
        )
    return state.gateway
