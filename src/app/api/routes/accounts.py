from fastapi import APIRouter, Depends

from app.api.dependencies import get_gateway
from app.core.config import get_settings
from app.schemas.accounts import AccountInfo, AccountsInfoResponse
from app.services.ctrader_gateway import CTraderGateway

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/info", response_model=AccountsInfoResponse)
def get_accounts_info(gateway: CTraderGateway = Depends(get_gateway)) -> AccountsInfoResponse:
    settings = get_settings()
    accounts = gateway.get_accounts()
    trader_info = gateway.get_trader_info(settings.ctrader_account_id)
    return AccountsInfoResponse(
        default_account_id=settings.ctrader_account_id,
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
