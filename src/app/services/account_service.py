from app.core.config import Settings
from app.schemas.accounts import AccountInfo, AccountsInfoResponse
from app.services.ctrader import CTraderGateway


class AccountService:
    def __init__(self, gateway: CTraderGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._settings = settings

    def get_accounts_info(self) -> AccountsInfoResponse:
        accounts = self._gateway.get_accounts()
        trader_info = self._gateway.get_trader_info(self._settings.ctrader_account_id)
        return AccountsInfoResponse(
            default_account_id=self._settings.ctrader_account_id,
            accounts=[
                AccountInfo(
                    account_id=account.account_id,
                    is_live=account.is_live,
                    trader_login=account.trader_login,
                )
                for account in accounts
            ],
            trader=trader_info,
        )
