from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOASymbolByIdReq,
    ProtoOASymbolByIdRes,
    ProtoOASymbolsListReq,
    ProtoOASymbolsListRes,
)

from app.services.ctrader.models import CTraderSymbol
from app.services.ctrader.transport import CTraderTransport
from app.services.exceptions import CTraderServiceError


class CTraderSymbolClient:
    def __init__(self, transport: CTraderTransport) -> None:
        self._transport = transport

    def resolve_symbol_id(self, account_id: int, symbol_name: str) -> tuple[int, str]:
        req = ProtoOASymbolsListReq()
        req.ctidTraderAccountId = account_id
        req.includeArchivedSymbols = False
        response = self._transport.request(req, expected_types=(ProtoOASymbolsListRes,))

        target = symbol_name.strip().upper()
        for symbol in response.symbol:
            if symbol.symbolName.upper() == target:
                return symbol.symbolId, symbol.symbolName
        raise CTraderServiceError(f"Symbol '{symbol_name}' not found for account {account_id}.")

    def get_symbol_details(self, account_id: int, symbol_id: int) -> CTraderSymbol:
        req = ProtoOASymbolByIdReq()
        req.ctidTraderAccountId = account_id
        req.symbolId.append(symbol_id)
        response = self._transport.request(req, expected_types=(ProtoOASymbolByIdRes,))
        if not response.symbol:
            raise CTraderServiceError(f"Symbol id '{symbol_id}' not found for account {account_id}.")
        symbol = response.symbol[0]
        return CTraderSymbol(
            symbol_id=symbol.symbolId,
            symbol_name="",
            digits=symbol.digits,
            lot_size=symbol.lotSize,
            step_volume=symbol.stepVolume,
            min_volume=symbol.minVolume,
            max_volume=symbol.maxVolume,
        )

    def get_symbol_map(self, account_id: int) -> dict[int, str]:
        req = ProtoOASymbolsListReq()
        req.ctidTraderAccountId = account_id
        req.includeArchivedSymbols = False
        response = self._transport.request(req, expected_types=(ProtoOASymbolsListRes,))
        return {symbol.symbolId: symbol.symbolName for symbol in response.symbol}
