from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "cTrader API"
    app_version: str = "0.1.0"
    environment: str = "dev"

    ctrader_host: str = Field(default="demo", alias="CTRADER_HOST")
    ctrader_client_id: str = Field(alias="CTRADER_CLIENT_ID")
    ctrader_client_secret: str = Field(alias="CTRADER_CLIENT_SECRET")
    ctrader_access_token: str = Field(alias="CTRADER_ACCESS_TOKEN")
    ctrader_account_id: int = Field(alias="CTRADER_ACCOUNT_ID")
    ctrader_request_timeout_seconds: float = Field(default=15.0, alias="CTRADER_REQUEST_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
