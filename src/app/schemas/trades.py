from typing import Literal

from pydantic import BaseModel, Field


class PlaceTradeRequest(BaseModel):
    symbol_name: str = Field(..., min_length=1, description="cTrader symbol name, e.g. EURUSD.")
    side: Literal["BUY", "SELL"] = Field(..., description="Trade side.")
    volume_lots: float = Field(..., gt=0, description="Trade volume in lots, e.g. 1 or 0.1.")
    label: str | None = Field(default=None, max_length=50)
    comment: str | None = Field(default=None, max_length=100)


class PlaceTradeResponse(BaseModel):
    account_id: int
    symbol_id: int
    symbol_name: str
    volume_lots: float
    volume_units: int
    execution: dict
