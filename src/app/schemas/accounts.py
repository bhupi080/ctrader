from pydantic import BaseModel


class AccountInfo(BaseModel):
    account_id: int
    is_live: bool
    trader_login: str | None = None


class AccountsInfoResponse(BaseModel):
    default_account_id: int
    accounts: list[AccountInfo]
    trader: dict
