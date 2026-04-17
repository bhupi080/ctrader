# cTrader Open API starter (uv)

This project provides a minimal Python starter for connecting to cTrader Open API via the official Python SDK.

## 1) Install dependencies

```powershell
uv sync
```

## 2) Configure environment

Copy `.env.example` to `.env` and fill values:

- `CTRADER_HOST`: `demo` or `live`
- `CTRADER_CLIENT_ID`: Open API app client ID
- `CTRADER_CLIENT_SECRET`: Open API app client secret
- `CTRADER_ACCOUNT_ID`: your cTrader account ID (integer)
- `CTRADER_ACCESS_TOKEN`: cTrader ID OAuth access token

## 3) Run

```powershell
uv run main.py
```

Expected successful flow:

1. Connect to endpoint
2. Application auth success
3. Account auth success

## Notes

- This flow uses cTrader ID access token for account auth.
- If you only have broker password, generate OAuth token first in the cTrader Open API auth flow.
