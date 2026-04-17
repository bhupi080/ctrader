from google.protobuf.json_format import MessageToDict

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAExecutionEvent,
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
