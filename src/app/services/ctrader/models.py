from dataclasses import dataclass


@dataclass
class CTraderAccount:
    account_id: int
    is_live: bool
    trader_login: str | None


@dataclass
class CTraderSymbol:
    symbol_id: int
    symbol_name: str
    digits: int
    lot_size: int
    step_volume: int
    min_volume: int
    max_volume: int
