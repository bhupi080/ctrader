from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException

from app.services.ctrader import CTraderGateway
from app.services.signal_account_map import SignalAccountMap, SignalAccountMapError


class TradeHistoryService:
    def __init__(self, gateway: CTraderGateway, signal_account_map: SignalAccountMap) -> None:
        self._gateway = gateway
        self._signal_account_map = signal_account_map

    def get_all_trades(self, signal_type: str, from_date: date | None, to_date: date | None) -> list[dict]:
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

        try:
            account_id = self._signal_account_map.resolve_account_id(signal_type)
        except SignalAccountMapError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        self._gateway.ensure_account_authorized(account_id)
        return self._gateway.get_deal_history(account_id, from_date, to_date)
