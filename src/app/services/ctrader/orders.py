from google.protobuf.json_format import MessageToDict

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAmendPositionSLTPReq,
    ProtoOAClosePositionReq,
    ProtoOAExecutionEvent,
    ProtoOAReconcileReq,
    ProtoOAReconcileRes,
    ProtoOANewOrderReq,
    ProtoOAOrderErrorEvent,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOAOrderType, ProtoOATradeSide

from app.services.ctrader.transport import CTraderTransport
from app.services.exceptions import CTraderApiError


class CTraderOrderClient:
    def __init__(self, transport: CTraderTransport) -> None:
        self._transport = transport

    def place_market_order(
        self,
        account_id: int,
        symbol_id: int,
        side: str,
        volume: int,
        label: str | None = None,
        comment: str | None = None,
    ) -> dict:
        req = ProtoOANewOrderReq()
        req.ctidTraderAccountId = account_id
        req.symbolId = symbol_id
        req.orderType = ProtoOAOrderType.Value("MARKET")
        req.tradeSide = ProtoOATradeSide.Value(side.upper())
        req.volume = volume
        if label:
            req.label = label
        if comment:
            req.comment = comment

        response = self._transport.request(
            req,
            expected_types=(ProtoOAExecutionEvent, ProtoOAOrderErrorEvent),
        )
        if isinstance(response, ProtoOAOrderErrorEvent):
            raise CTraderApiError(response.errorCode, response.description or "Order rejected.")
        return MessageToDict(response, preserving_proto_field_name=True)

    def get_open_positions(self, account_id: int) -> list[dict]:
        req = ProtoOAReconcileReq()
        req.ctidTraderAccountId = account_id
        response = self._transport.request(req, expected_types=(ProtoOAReconcileRes,))
        return [
            {
                "position_id": position.positionId,
                "volume": position.tradeData.volume,
                "symbol_id": position.tradeData.symbolId,
                "trade_side": position.tradeData.tradeSide,
            }
            for position in response.position
        ]

    def close_position(
        self,
        account_id: int,
        position_id: int,
        volume: int,
    ) -> dict:
        req = ProtoOAClosePositionReq()
        req.ctidTraderAccountId = account_id
        req.positionId = position_id
        req.volume = volume
        response = self._transport.request(
            req,
            expected_types=(ProtoOAExecutionEvent, ProtoOAOrderErrorEvent),
        )
        if isinstance(response, ProtoOAOrderErrorEvent):
            raise CTraderApiError(response.errorCode, response.description or "Close position rejected.")
        return MessageToDict(response, preserving_proto_field_name=True)

    def amend_position_take_profit(
        self,
        account_id: int,
        position_id: int,
        take_profit: float | None,
    ) -> dict:
        req = ProtoOAAmendPositionSLTPReq()
        req.ctidTraderAccountId = account_id
        req.positionId = position_id
        if take_profit is not None:
            req.takeProfit = take_profit
        response = self._transport.request(
            req,
            expected_types=(ProtoOAExecutionEvent, ProtoOAOrderErrorEvent),
        )
        if isinstance(response, ProtoOAOrderErrorEvent):
            raise CTraderApiError(response.errorCode, response.description or "Amend take profit rejected.")
        return MessageToDict(response, preserving_proto_field_name=True)
