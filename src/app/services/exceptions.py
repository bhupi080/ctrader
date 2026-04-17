class CTraderServiceError(Exception):
    """Base cTrader integration error."""


class CTraderTimeoutError(CTraderServiceError):
    """Raised when Open API request times out."""


class CTraderApiError(CTraderServiceError):
    """Raised when Open API returns an error response."""

    def __init__(self, code: str, description: str) -> None:
        super().__init__(f"{code}: {description}")
        self.code = code
        self.description = description
