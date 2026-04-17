# cTrader Trading API (FastAPI + Open API)

Structured FastAPI service built on top of the official cTrader Open API Python SDK.

## Architecture

The codebase follows a scalable layout:

- `src/app/api` - HTTP routing layer
- `src/app/schemas` - request/response contracts
- `src/app/services` - cTrader gateway and business logic
- `src/app/core` - settings and application state

## Setup

1. Install dependencies:

```powershell
uv sync
```

2. Copy `.env.example` to `.env` and set values:

- `CTRADER_HOST` (`demo` or `live`)
- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_ACCOUNT_ID`
- `CTRADER_ACCESS_TOKEN`
- `CTRADER_REQUEST_TIMEOUT_SECONDS` (optional)

3. Start API server:

```powershell
uv run main.py
```

Server runs at `http://localhost:8000` by default.

## Endpoints (v1)

- `GET /health` - health check
- `GET /api/v1/accounts/info` - list token-linked accounts and trader details
- `POST /api/v1/trades` - place market order on configured account

## Trade Request Example

```json
{
  "symbol_name": "EURUSD",
  "side": "BUY",
  "volume_lots": 0.1,
  "label": "test-order",
  "comment": "api test"
}
```

## Important Notes

- Keep trading calls on demo until fully validated.
- Open API limits still apply (50 req/s non-historical, 5 req/s historical per connection).
- Use OAuth access token flow as documented by cTrader.
