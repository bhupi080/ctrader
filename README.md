# Trading Automation Project: TradingView X cTrader

Production-style algorithmic trading bridge that receives TradingView webhook signals and executes trades on cTrader (FXPro broker) using the cTrader Open API.

This project demonstrates end-to-end trading automation, secure API design, cloud deployment on AWS (Ubuntu), and operational controls for multi-account routing.

## End-to-End Flowchart

```text
+-----------------------------------+
|            TradingView            |
|  Pine Strategy (Black Box)        |
|  -> Webhook Payload               |
|  (symbol, size, strategy, signal) |
+-------------------+---------------+
                    |
                    v
+-----------------------------------+
|      Cloudflare Edge Security     |
|  Route + Firewall + Whitelist     |
+-------------------+---------------+
                    |
          +---------+---------+
          | Whitelisted Source?|
          +---------+---------+
                    |
          +---------+---------+
          |                   |
         Yes                 No
          |                   |
          v                   v
+------------------------+   +------------------------+
| AWS EC2 Ubuntu         |   | Blocked / Dropped      |
| FastAPI Trading API    |   | (request rejected)     |
+-----------+------------+   +------------------------+
            |
            v
+-----------------------------------+
| Validate + Normalize Request      |
+-------------------+---------------+
                    |
                    v
+-----------------------------------+
| Map signal_type -> account_id     |
| (signal_account_map.yml)          |
+-------------------+---------------+
                    |
                    v
          +---------+---------+
          | FXPro Symbol      |
          | Mapping Enabled?  |
          +---------+---------+
                    |
          +---------+---------+
          |                   |
         Yes                 No
          |                   |
          v                   v
+------------------------+   +------------------------+
| Map Symbol via JSON    |   | Use Original Symbol    |
| mapping file           |   |                        |
+-----------+------------+   +-----------+------------+
            \                          /
             \                        /
              v                      v
        +------------------------------+
        | cTrader Gateway              |
        | Authorize + Execute Trade    |
        +---------------+--------------+
                        |
                        v
        +------------------------------+
        | cTrader Open API             |
        +---------------+--------------+
                        |
                        v
        +------------------------------+
        | FXPro Broker Account         |
        | Order / Position Updated     |
        +---------------+--------------+
                        |
                        v
        +------------------------------+
        | API Response + Logs          |
        +------------------------------+
```

## Project Overview

The strategy logic is written in Pine Script on TradingView (treated as a black box by this service).  
When the strategy emits a signal, TradingView sends a payload to this API containing fields such as:

- `symbol`
- `order size`
- `strategy name`
- `signal` (`BUY` / `SELL`)

The API validates and transforms the payload, resolves the target account, and executes the trade on cTrader via FXPro.

## Why This Project Matters (Resume Highlights)

- Built a real-world low-latency bridge between TradingView alerts and cTrader execution.
- Designed secure webhook ingestion with network-level access controls and source restriction.
- Deployed and operated the service on AWS Ubuntu with Cloudflare routing.
- Implemented account and symbol mapping to support broker-specific execution behavior.
- Exposed a robust trade operations API (open, close, modify SL/TP, history retrieval).

## High-Level Architecture

- **Signal Source:** TradingView strategy alerts (Pine Script)
- **Execution API:** FastAPI service in this repository
- **Trading Backend:** cTrader Open API integration
- **Broker:** FXPro
- **Hosting:** AWS EC2 (Ubuntu)
- **Edge/Routing:** Cloudflare (restricted entry path)

Flow:

1. TradingView sends webhook payload.
2. Request reaches Cloudflare-routed endpoint.
3. API accepts only approved/whitelisted signal traffic.
4. `signal_type` is mapped to broker account ID.
5. Symbol mapping is applied if enabled.
6. Order is placed/managed in cTrader for the mapped FXPro account.

## Security Model

This implementation is designed so only trusted trading signals are accepted:

- Cloudflare-based routing and perimeter filtering.
- Webhook endpoint restricted to approved source behavior.
- Non-whitelisted traffic blocked before trade execution path.
- Environment-based secret management for cTrader credentials and tokens.
- Explicit account routing map to prevent accidental cross-account execution.

## Core Technical Stack

- Python 3.12
- FastAPI + Uvicorn
- cTrader Open API Python SDK
- Pydantic / pydantic-settings
- YAML and JSON config-driven routing/mapping

## Repository Structure

- `src/app/api` - HTTP routing layer
- `src/app/schemas` - request/response contracts
- `src/app/services` - trade orchestration and domain services
- `src/app/services/ctrader` - cTrader transport/protocol clients
- `src/app/core` - settings and application state
- `signal_account_map.yml` - signal-to-account routing
- `pepperstone_to_fxpro_mapping.json` - optional symbol translation map

## API Capabilities

- Health check and account info
- Place market orders by signal/account mapping
- Close all positions / by ticket / by symbol
- Set/remove take-profit
- Set/remove stop-loss
- Retrieve trade history by date range and signal type

## Configuration

Copy `.env.example` to `.env` and configure:

- `CTRADER_HOST` (`demo` or `live`)
- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_ACCOUNT_ID`
- `CTRADER_ACCESS_TOKEN`
- `CTRADER_REQUEST_TIMEOUT_SECONDS`
- `SIGNAL_ACCOUNT_MAP_PATH`
- `FXPRO_SYMBOL_MAPPING_ENABLED`
- `SYMBOL_MAPPING_PATH`

Configure signal routing in `signal_account_map.yml`:

```yaml
K: 47032097
C2: 47061734
```

Optional symbol normalization for broker compatibility is controlled by `FXPRO_SYMBOL_MAPPING_ENABLED` and `SYMBOL_MAPPING_PATH`.

## Local Run

Install dependencies:

```powershell
uv sync
```

Run server:

```powershell
uv run main.py
```

Default local host: `http://localhost:80`

## Sample Trade Payload

```json
{
  "signal_type": "K",
  "symbol_name": "EURUSD",
  "signal": "BUY",
  "volume_lots": 0.1,
  "label": "tv-strategy-order",
  "comment": "TradingView automation"
}
```

`signal` is case-insensitive and supports aliases such as `long` / `short`.

## Production Notes

- Keep strict separation between `demo` and `live` environments.
- Restart service after mapping file updates to refresh cached config.
- Validate all `signal_type` routes before going live.
- Monitor cTrader API rate limits and request timeouts.

## Portfolio / Resume Title Suggestion

**Trading Automation Project - TradingView X cTrader (AWS + Cloudflare + FXPro)**

Short description you can reuse:

> Developed a secure, cloud-hosted trading automation bridge that converts TradingView Pine strategy alerts into live cTrader executions on FXPro accounts, with account routing, symbol normalization, and full trade lifecycle APIs.
