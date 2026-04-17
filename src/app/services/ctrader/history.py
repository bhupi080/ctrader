from datetime import UTC, date, datetime

from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOADealListReq,
    ProtoOADealListRes,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATradeSide

from app.services.ctrader.symbols import CTraderSymbolClient
from app.services.ctrader.transport import CTraderTransport


class CTraderHistoryClient:
    def __init__(self, transport: CTraderTransport, symbols: CTraderSymbolClient) -> None:
        self._transport = transport
        self._symbols = symbols

    def get_deal_history(
        self,
        account_id: int,
        from_date: date,
        to_date: date,
        max_rows: int = 5000,
    ) -> list[dict]:
        from_ts_ms = int(
            datetime.combine(from_date, datetime.min.time(), tzinfo=UTC).timestamp() * 1000
        )
        to_ts_ms = int(
            datetime.combine(to_date, datetime.max.time(), tzinfo=UTC).timestamp() * 1000
        )
        symbol_map = self._symbols.get_symbol_map(account_id)

        req = ProtoOADealListReq()
        req.ctidTraderAccountId = account_id
        req.fromTimestamp = from_ts_ms
        req.toTimestamp = to_ts_ms
        req.maxRows = max_rows
        response = self._transport.request(req, expected_types=(ProtoOADealListRes,))

        by_position: dict[int, list] = {}
        for deal in response.deal:
            if deal.positionId <= 0:
                continue
            by_position.setdefault(deal.positionId, []).append(deal)

        trades: list[dict] = []
        for position_id in sorted(by_position.keys()):
            position_deals = by_position[position_id]
            if not position_deals:
                continue

            close_deals = [d for d in position_deals if d.HasField("closePositionDetail")]
            if not close_deals:
                continue

            open_deal = min(position_deals, key=lambda d: d.executionTimestamp or d.createTimestamp)
            close_deal = max(close_deals, key=lambda d: d.executionTimestamp or d.createTimestamp)
            close_detail = close_deal.closePositionDetail

            symbol_name = symbol_map.get(close_deal.symbolId, str(close_deal.symbolId))
            symbol_details = self._symbols.get_symbol_details(account_id, close_deal.symbolId)
            lot_size = max(1, symbol_details.lot_size)
            size_lots = close_detail.closedVolume / lot_size

            gross_profit = self._money_from_int(close_detail.grossProfit, close_detail.moneyDigits)
            swap = self._money_from_int(close_detail.swap, close_detail.moneyDigits)
            commission = self._money_from_int(close_detail.commission, close_detail.moneyDigits)
            pnl = gross_profit + swap + commission

            open_ts_s = int((open_deal.executionTimestamp or open_deal.createTimestamp) / 1000)
            close_ts_s = int((close_deal.executionTimestamp or close_deal.createTimestamp) / 1000)
            trade_type = "buy" if open_deal.tradeSide == ProtoOATradeSide.Value("BUY") else "sell"

            trades.append(
                {
                    "ticketNumber": position_id,
                    "openTime": open_ts_s,
                    "openedAt": self._fmt_ts(open_ts_s),
                    "closeTime": close_ts_s,
                    "closedAt": self._fmt_ts(close_ts_s),
                    "symbol": symbol_name,
                    "pnl": round(pnl, 10),
                    "swap": round(swap, 10),
                    "size": round(size_lots, 10),
                    "commission": round(commission, 10),
                    "profit": round(gross_profit, 10),
                    "type": trade_type,
                    "entryPrice": round(float(open_deal.executionPrice), 10),
                    "exitPrice": round(float(close_deal.executionPrice), 10),
                }
            )

        trades.sort(key=lambda item: item.get("openTime", 0))
        return trades

    @staticmethod
    def _money_from_int(value: int, money_digits: int) -> float:
        return value / (10**max(money_digits, 0))

    @staticmethod
    def _fmt_ts(ts_seconds: int) -> str:
        return datetime.fromtimestamp(ts_seconds, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
