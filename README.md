# cTrader Trading API (FastAPI + Open API)

Structured FastAPI service built on top of the official cTrader Open API Python SDK.

## Architecture

The codebase follows a scalable layout:

- `src/app/api` - HTTP routing layer
- `src/app/schemas` - request/response contracts
- `src/app/services` - domain services and orchestration
- `src/app/services/ctrader` - cTrader Open API transport and protocol clients
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
- `SIGNAL_ACCOUNT_MAP_PATH` (optional; defaults to `signal_account_map.yml`)
- `FXPRO_SYMBOL_MAPPING_ENABLED` (optional; defaults to `false`)
- `SYMBOL_MAPPING_PATH` (optional; defaults to `pepperstone_to_fxpro_mapping.json`)

3. Configure `signal_type -> account_id` map (root file `signal_account_map.yml`):

```yaml
K: 47032097
C2: 47061734
# add more signal mappings
```

4. Start API server:

```powershell
uv run main.py
```

Server runs at `http://localhost:80` by default.

## Endpoints

- `GET /health` - health check
- `GET /api/account/info` - list token-linked accounts and trader details
- `POST /api/trade` - place market order by `signal_type`
- `POST /api/trade/close-all` - close all positions by `signal_type`
- `POST /api/trade/close-by-ticket` - close specific tickets by `signal_type`
- `POST /api/trade/close-by-symbol` - close by symbol+direction for `signal_type`
- `GET /api/trade/all-trades` - trade history by `signal_type`
- `POST /api/trade/set-take-profit` - set TP by `signal_type`
- `POST /api/trade/remove-take-profit` - remove TP by `signal_type`
- `POST /api/trade/remove-all-take-profit` - remove TP from all positions by `signal_type`
- `POST /api/trade/set-stop-loss` - set SL by `signal_type`
- `POST /api/trade/remove-stop-loss` - remove SL by `signal_type`
- `POST /api/trade/remove-all-stop-loss` - remove SL from all positions by `signal_type`

## Trade Request Example

```json
{
  "signal_type": "K",
  "symbol_name": "EURUSD",
  "signal": "BUY",
  "volume_lots": 0.1,
  "label": "test-order",
  "comment": "api test"
}
```

`signal` is case-insensitive and also accepts `long`/`short` aliases.

When `FXPRO_SYMBOL_MAPPING_ENABLED=true`, symbol-based endpoints map source symbols
using `SYMBOL_MAPPING_PATH` before resolution (e.g. `BTCUSD -> BITCOIN`).
If a symbol is not found in the mapping file, the original symbol is used.

## Additional Request Examples

Close all for one mapped signal:

```json
{
  "signal_type": "C2"
}
```

Set stop loss:

```json
{
  "signal_type": "K",
  "ticket": 123456789,
  "stop_loss": 1.095
}
```

Get history:

`GET /api/trade/all-trades?signal_type=K&from=2026-04-01&to=2026-04-20`

## Important Notes

- Keep trading calls on demo until fully validated.
- Open API limits still apply (50 req/s non-historical, 5 req/s historical per connection).
- Use OAuth access token flow as documented by cTrader.
- Unknown `signal_type` returns HTTP 400.
- Symbol mapping is applied only to symbol-based actions (`/trade` and `/trade/close-by-symbol`) when enabled.
