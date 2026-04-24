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

_UNSET = object()


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
                "comment": self._read_text_field(position, position.tradeData, field_name="comment"),
                "trade_comment": self._read_text_field(position.tradeData, position, field_name="comment"),
                "label": self._read_text_field(position, position.tradeData, field_name="label"),
                "trade_label": self._read_text_field(position.tradeData, position, field_name="label"),
                "has_stop_loss": self._has_field(position, "stopLoss"),
                "has_take_profit": self._has_field(position, "takeProfit"),
                "stop_loss": position.stopLoss if self._has_field(position, "stopLoss") else None,
                "take_profit": position.takeProfit if self._has_field(position, "takeProfit") else None,
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
        if take_profit is None:
            return self.amend_position_sltp(account_id, position_id)
        return self.amend_position_sltp(account_id, position_id, take_profit=take_profit)

    def amend_position_stop_loss(
        self,
        account_id: int,
        position_id: int,
        stop_loss: float | None,
    ) -> dict:
        if stop_loss is None:
            return self.amend_position_sltp(account_id, position_id)
        return self.amend_position_sltp(account_id, position_id, stop_loss=stop_loss)

    def amend_position_sltp(
        self,
        account_id: int,
        position_id: int,
        stop_loss: float | object = _UNSET,
        take_profit: float | object = _UNSET,
    ) -> dict:
        req = ProtoOAAmendPositionSLTPReq()
        req.ctidTraderAccountId = account_id
        req.positionId = position_id
        if stop_loss is not _UNSET:
            req.stopLoss = stop_loss
        if take_profit is not _UNSET:
            req.takeProfit = take_profit
        response = self._transport.request(req, expected_types=(ProtoOAExecutionEvent, ProtoOAOrderErrorEvent))
        if isinstance(response, ProtoOAOrderErrorEvent):
            raise CTraderApiError(response.errorCode, response.description or "Amend position SL/TP rejected.")
        return MessageToDict(response, preserving_proto_field_name=True)

    @staticmethod
    def _has_field(message, field_name: str) -> bool:
        try:
            return message.HasField(field_name)
        except ValueError:
            return False

    @staticmethod
    def _read_text_field(*objects, field_name: str) -> str:
        for obj in objects:
            if obj is None:
                continue
            value = getattr(obj, field_name, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
