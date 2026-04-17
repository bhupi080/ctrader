from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException

from app.core.config import Settings
from app.services.ctrader import CTraderGateway


class TradeHistoryService:
    def __init__(self, gateway: CTraderGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._settings = settings

    def get_all_trades(self, from_date: date | None, to_date: date | None) -> list[dict]:
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

        return self._gateway.get_deal_history(self._settings.ctrader_account_id, from_date, to_date)
