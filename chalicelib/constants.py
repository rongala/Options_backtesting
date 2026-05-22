# Database Configuration
DB_STAGE_LOCAL = 'LOCAL'
DB_STAGE_DEV = 'DEV'

# Default values
DEFAULT_OPTION_EXPIRY_DATE = -999
DEFAULT_OPTION_STRIKE = -999
DEFAULT_OPTION_TYPE = 'N/A'

# Query field values
FIELD_CURRENT_PRICE = '31'
FIELD_BID_ASK = '84,86'
FIELD_BID = '84'
FIELD_ASK = '86'

# Order types
ORDER_TYPE_BUY = 'BUY'
ORDER_TYPE_SELL = 'SELL'
SECTYPE_STOCK = 'STK'
SECTYPE_OPTION = 'OPT'

# Error messages
ERROR_MISSING_PARAMS = "Missing Parameters: "
ERROR_CONTRACT_NOT_FOUND = "Contract ID doesn't exist in Database"
ERROR_NO_BALANCE = "No balance found for this account {account_id}. may be it is not seeded."
ERROR_NEGATIVE_BALANCE = "This order causing -ve balance, deducting {amount}. NOTE: This error is not handled in IBKR API"
ERROR_INSUFFICIENT_POSITIONS = "Not enough positions to sell '{quantity}'"
ERROR_INVALID_ORDER_SIDE = "Invalid order/opt side. It has to be either BUY or SELL"
ERROR_UNABLE_TO_INSERT_ORDER = "Unable to insert into order history and create order id"

# Contract IDs
SPY_CON_ID = 756733

# Tables
TABLE_SIM_STRIKES = 'public.sim_strikes'
TABLE_SIM_CONTRACTS = 'public.sim_contracts'
TABLE_SIM_STOCK_HISTORY = 'public.sim_stock_history'
TABLE_SIM_OPTION_HISTORY = 'public.sim_option_history'
TABLE_SIM_POSITIONS = 'public.sim_positions'
TABLE_ORDER_HISTORY = 'public.order_history'
TABLE_LEDGER_HISTORY = 'public.ledger_history'
