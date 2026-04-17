from app.core.config import Settings
from app.schemas.trades import PlaceTradeRequest, PlaceTradeResponse
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
