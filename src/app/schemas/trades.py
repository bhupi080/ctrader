from typing import Literal

from pydantic import BaseModel, Field


class PlaceTradeRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
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


class CloseAllTradesResponse(BaseModel):
    account_id: int
    requested_tickets: list[int] | None = None
    closed_tickets: list[int]
    executions: list[dict]
    skipped_tickets: list[dict] = Field(
        default_factory=list,
        description="Tickets skipped due to API/business errors (e.g. MARKET_CLOSED).",
    )
    not_found_tickets: list[int] = Field(
        default_factory=list,
        description="Requested tickets that were not found among currently open positions.",
    )


class CloseByTicketRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
    tickets: list[int] = Field(..., min_length=1, description="Position IDs (ticket numbers) to close.")


class CloseByTicketResponse(CloseAllTradesResponse):
    pass


class CloseBySymbolRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
    symbol_name: str = Field(..., min_length=1, description="cTrader symbol name, e.g. BTCUSD.")
    direction: Literal["LONG", "SHORT", "ALL"] = Field(
        ...,
        description="LONG: BUY positions only, SHORT: SELL only, ALL: both sides on this symbol.",
    )


class CloseBySymbolResponse(CloseAllTradesResponse):
    symbol_name: str
    symbol_id: int
    requested_direction: Literal["LONG", "SHORT", "ALL"]


class CloseAllTradesRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")


class SetTakeProfitRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
    ticket: int = Field(..., gt=0, description="Position ID (ticket number).")
    take_profit: float = Field(..., gt=0, description="Take-profit target price.")


class RemoveTakeProfitRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
    ticket: int = Field(..., gt=0, description="Position ID (ticket number).")


class TakeProfitResponse(BaseModel):
    account_id: int
    ticket: int
    execution: dict


class RemoveAllTakeProfitRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")


class RemoveAllTakeProfitResponse(BaseModel):
    account_id: int
    updated_tickets: list[int]
    executions: list[dict]
    skipped_tickets: list[dict] = Field(
        default_factory=list,
        description="Tickets skipped due to API/business errors.",
    )


class SetStopLossRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
    ticket: int = Field(..., gt=0, description="Position ID (ticket number).")
    stop_loss: float = Field(..., gt=0, description="Stop-loss target price.")


class RemoveStopLossRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")
    ticket: int = Field(..., gt=0, description="Position ID (ticket number).")


class StopLossResponse(BaseModel):
    account_id: int
    ticket: int
    execution: dict


class RemoveAllStopLossRequest(BaseModel):
    signal_type: str = Field(..., min_length=1, description="Signal type mapped to cTrader account ID.")


class RemoveAllStopLossResponse(BaseModel):
    account_id: int
    updated_tickets: list[int]
    executions: list[dict]
    skipped_tickets: list[dict] = Field(
        default_factory=list,
        description="Tickets skipped due to API/business errors.",
    )
