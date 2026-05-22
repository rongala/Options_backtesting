# Sim API REST Service

SIMAPI simulates a subset of the IBKR Client Portal REST API against a PostgreSQL back-testing database. It provides time-travel capabilities so trading algorithms can be tested against historical data without a live brokerage connection.

Built with [AWS Chalice](https://aws.github.io/chalice/quickstart.html), deployable as AWS Lambda + API Gateway.

---

## Project Structure

```
sim-api-rest-service/
├── app.py                    # Chalice routes
├── requirements.txt
├── chalicelib/
│   ├── lambda_handlers.py    # Endpoint handlers (PortalDB + PortalService wiring)
│   ├── service.py            # Business logic
│   ├── repository.py         # Database access (PortalDB context manager)
│   ├── utils.py              # DB helpers: connect, query, insert order/ledger
│   ├── constants.py          # Shared constants and error messages
│   ├── config.py             # ConfigManager: env vars → config.ini fallback
│   ├── setup_logger.py       # Logging setup
│   └── config.ini            # Local-only fallback config (not committed)
├── db_migration/             # SQL migration and seed scripts
└── tests/
```

---

## Architecture

```
app.py (Chalice routes)
    └── lambda_handlers.py
            └── PortalDB (context manager — connection lifecycle)
                    └── PortalService (business logic)
                            └── PortalDB methods (SQL via parameterized queries)
```

`PortalDB` opens a connection on `__enter__` and commits/rolls back on `__exit__`. All handlers follow the same pattern:

```python
with PortalDB(event["stage"]) as db:
    svc = PortalService(db)
    output = svc.some_method(event)
```

---

## Prerequisites

- Python 3.8+
- `virtualenv` / `venv`
- PostgreSQL database with `sim_*` schema tables seeded
- For LOCAL stage: SSH bastion access and a private key

---

## Installation

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration

Configuration is resolved in priority order: **environment variable → `config.ini`**.

### Environment variables

| Variable | Description | Required for |
|---|---|---|
| `RDS_HOST` | RDS database host | DEV / PROD |
| `RDS_USERNAME` | RDS username | DEV / PROD |
| `RDS_USER_PWD` | RDS password | DEV / PROD |
| `RDS_DB_NAME` | RDS database name | DEV / PROD |
| `SSH_HOST` | SSH bastion host | LOCAL |
| `SSH_USERNAME` | SSH user | LOCAL |
| `SSH_PRIVATE_KEY` | Path to SSH private key | LOCAL |
| `REMOTE_BIND_ADDRESS` | Remote DB host (behind bastion) | LOCAL |
| `REMOTE_BIND_PORT` | Remote DB port (default: `5432`) | LOCAL |
| `LOCAL_BIND_ADDRESS` | Local tunnel bind address (default: `localhost`) | LOCAL |
| `LOCAL_BIND_PORT` | Local tunnel bind port (default: `6543`) | LOCAL |
| `SSH_DB_NAME` | DB name used over SSH | LOCAL |
| `SSH_DB_USER` | DB user used over SSH | LOCAL |
| `SSH_DB_PASSWORD` | DB password used over SSH | LOCAL |

### `config.ini` (local development only)

Place a `chalicelib/config.ini` with sections `[local]` and `[dev]` to avoid setting environment variables during local development. Do not commit this file.

---

## Running Locally

```bash
chalice local
```

The server starts at `http://127.0.0.1:8000`.

Every request requires a `stage` parameter (`local`, `dev`, or `prod`) so the handler knows which database connection to open.

---

## Deployment

```bash
# Test deploy to a staging slot before promoting
chalice deploy --profile devwest --stage test

# Deploy to dev/west
chalice deploy --profile devwest
```

---

## API Endpoints

> **Note:** Every request must include `stage=local|dev|prod` as a query parameter (or in the JSON body for POST requests). This controls which database connection is used.

### Strikes

```
GET /v1/api/iserver/secdef/strikes
```

Query params: `conid`, `month`, `stage`

Sample response:
```json
{"call": ["252.50", "150.00"], "put": ["198.00", "140.50"]}
```

---

### Option Contract Info

```
GET /v1/api/iserver/secdef/info
```

Query params: `conid`, `month`, `strike`, `right`, `stage`

Sample response:
```json
[{"conid": 2015120410018900, "strike": "189", "right": "C", "maturityDate": 20151204}]
```

---

### Market Data Snapshot

```
GET /v1/api/iserver/marketdata/snapshot
```

Query params: `conids`, `quotetime`, `fields`, `stage`

`fields` values:
- `31` — last price
- `84,86` — bid and ask

Sample responses:
```json
[{"conid": 2013062810011100, "31": "329.56"}]
[{"conid": 2013062810011100, "84": "47.8500", "86": "52.0000"}]
```

---

### Place Order

```
POST /v1/api/iserver/account/{account_id}/order
```

JSON body:

| Field | Type | Description |
|---|---|---|
| `conid` | int | Contract ID |
| `cOID` | string | Client order ID |
| `parentId` | string | Parent order ID |
| `orderType` | string | `LIMIT` |
| `price` | decimal | Price per unit |
| `side` | string | `BUY` or `SELL` |
| `ticker` | string | e.g. `SPY` |
| `quantity` | decimal | Number of units |
| `secType` | string | `STK` or `OPT` |
| `quotetime` | string | `YYYY-MM-DD HH:MM:SS` |
| `stage` | string | `local`, `dev`, or `prod` |

Sample response:
```json
[{"order_id": 42, "local_order_id": "testOrd:C1", "order_status": "Filled"}]
```

---

### Ledger (Cash Balance + Net Liquidation)

```
GET /v1/api/portfolio/{account_id}/ledger
```

Query params: `quotetime`, `stage`

Sample response:
```json
{"account_id": "DU2387565", "USD": {"cashbalance": 85700.00, "netliquidationvalue": 91200.00}}
```

---

### Positions

```
GET /v1/api/portfolio/{account_id}/positions/{page_id}
```

Query params: `quotetime`, `stage`

---

### Settlement

```
POST /gkportal/{account_id}/settle
```

JSON body: `quotetime`, `stage`

Settles expiring options at end of day:
1. Identifies SELL obligations expiring on `quotetime` date.
2. Determines ITM/OTM based on EOD SPY price.
3. For ITM put (SELL): buys the underlying stock at strike.
4. For ITM call (SELL) with existing stock: sells the stock at strike.
5. Inserts order and ledger history records.
6. Expires all open option positions for that date.

---

### Compatibility Stubs

These return static or dummy responses to keep client bots running without errors:

| Method | Path |
|---|---|
| GET | `/v1/api/iserver/accounts` |
| GET | `/v1/api/portfolio/subaccounts` |
| POST | `/v1/api/iserver/secdef/search` |
| POST | `/v1/api/iserver/reply/{reply_id}` |
| GET | `/v1/api/sso/validate` |
| GET | `/v1/api/portfolio/{account_id}/positions/invalidate` |
| DELETE | `/v1/api/iserver/account/{account_id}/order/{order_id}` |
| GET | `/v1/api/iserver/account/orders` |

---

## Example Requests

```bash
# Strikes
curl "http://127.0.0.1:8000/v1/api/iserver/secdef/strikes?conid=756733&month=JAN98&stage=local"

# Option info
curl "http://127.0.0.1:8000/v1/api/iserver/secdef/info?conid=756733&month=JAN98&strike=110&right=C&stage=local"

# Last price snapshot
curl "http://127.0.0.1:8000/v1/api/iserver/marketdata/snapshot?conids=756733&fields=31&quotetime=1998-01-02%2009:00:00&stage=local"

# Bid/ask snapshot
curl "http://127.0.0.1:8000/v1/api/iserver/marketdata/snapshot?conids=1998010520011000&fields=84,86&quotetime=1998-01-02%2009:00:00&stage=local"

# Buy stock
curl -X POST http://127.0.0.1:8000/v1/api/iserver/account/DU2387565/order \
  -H "Content-Type: application/json" \
  -d '{
    "conid": 756733, "cOID": "testOrd:C1", "parentId": "testOrd:P1",
    "orderType": "LIMIT", "price": 290, "side": "BUY",
    "ticker": "SPY", "quantity": 100, "secType": "STK",
    "quotetime": "1998-01-02 09:00:00", "stage": "local"
  }'

# Ledger
curl "http://127.0.0.1:8000/v1/api/portfolio/DU2387565/ledger?quotetime=1998-01-02%2009:00:00&stage=local"

# Settlement
curl -X POST http://127.0.0.1:8000/gkportal/DU2387565/settle \
  -H "Content-Type: application/json" \
  -d '{"quotetime": "1998-01-05 16:15:00", "stage": "local"}'
```

---

## Database Schema Notes

All simulation tables use the `sim_` prefix in the `public` schema:

| Table | Purpose |
|---|---|
| `public.sim_strikes` | Available strikes per conid and month |
| `public.sim_contracts` | Option contract details |
| `public.sim_stock_history` | Historical stock prices |
| `public.sim_option_history` | Historical option bid/ask/last prices |
| `public.sim_positions` | Open positions per account |
| `public.sim_order_history` | Order audit trail |
| `public.sim_ledger_history` | Cash balance history |

SPY's underlying `conid` is `756733` (defined as `constants.SPY_CON_ID`).

---

## Testing

### Install test dependencies

```bash
pip install pytest pytest-mock pytest-cov
```

### Run the full suite

```bash
pytest tests/ -v
```

### Run a single test file

```bash
pytest tests/test_put_order.py -v
```

### Run a single test class

```bash
pytest tests/test_put_order.py::TestPutOrderBuyStk -v
```

### Run a single test by name (substring match)

```bash
pytest tests/ -k "test_buy_stk_returns_filled_status" -v
```

### Run with coverage report

```bash
pytest tests/ --cov=chalicelib --cov-report=term-missing
```

### Run only tests matching a component tag (marker)

If you add `@pytest.mark.<component>` decorators to tests:

```bash
pytest tests/ -m "execution_engine" -v
pytest tests/ -m "portfolio_tracker" -v
```

### Stop on first failure

```bash
pytest tests/ -x -v
```

### Run in parallel (requires `pytest-xdist`)

```bash
pip install pytest-xdist
pytest tests/ -n auto -v
```

Test scripts and seed data are under `tests/` and `db_migration/`.
