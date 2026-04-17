from fastapi import APIRouter, Depends

from app.api.dependencies import get_account_service
from app.schemas.accounts import AccountsInfoResponse
from app.services.account_service import AccountService

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/info", response_model=AccountsInfoResponse)
def get_accounts_info(service: AccountService = Depends(get_account_service)) -> AccountsInfoResponse:
    return service.get_accounts_info()
