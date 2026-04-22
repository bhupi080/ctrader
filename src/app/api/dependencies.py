from functools import lru_cache

from fastapi import HTTPException, status

from app.core import state
from app.core.config import get_settings
from app.services.ctrader import CTraderGateway
from app.services.account_service import AccountService
from app.services.signal_account_map import SignalAccountMap
from app.services.symbol_mapping import SymbolMapping
from app.services.trade_history_service import TradeHistoryService
from app.services.trade_service import TradeService


def get_gateway() -> CTraderGateway:
    if state.gateway is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="cTrader gateway is not initialized.",
        )
    return state.gateway


def get_account_service() -> AccountService:
    return AccountService(get_gateway(), get_settings())


@lru_cache
def get_signal_account_map() -> SignalAccountMap:
    settings = get_settings()
    return SignalAccountMap(settings.signal_account_map_path)


@lru_cache
def get_symbol_mapping() -> SymbolMapping:
    settings = get_settings()
    return SymbolMapping(settings.symbol_mapping_path)


def get_trade_service() -> TradeService:
    settings = get_settings()
    return TradeService(
        get_gateway(),
        get_signal_account_map(),
        get_symbol_mapping(),
        settings.fxpro_symbol_mapping_enabled,
    )


def get_trade_history_service() -> TradeHistoryService:
    return TradeHistoryService(get_gateway(), get_signal_account_map())
