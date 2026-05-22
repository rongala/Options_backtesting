import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Tuple, Dict, Any
from chalicelib.setup_logger import get_logger
from chalicelib.config import config_manager
from sshtunnel import SSHTunnelForwarder

logger = get_logger(__name__)


def get_db_conn(api_stage: str, tunnel: Optional[SSHTunnelForwarder] = None) -> psycopg2.extensions.connection:
    """
    Get database connection based on stage.
    
    @param api_stage: Stage name (LOCAL, DEV, PROD)
    @param tunnel: Optional SSH tunnel for local development
    @return: Database connection
    @raises: psycopg2.Error if connection fails
    """
    if api_stage.upper() == 'DEV':
        return get_db_conn_rds(api_stage)
    else:
        return get_db_conn_ssh(api_stage, tunnel)


def get_db_conn_rds(api_stage: str) -> psycopg2.extensions.connection:
    """
    Connect to RDS database directly.
    
    @param api_stage: Stage name
    @return: Database connection
    @raises: psycopg2.Error if connection fails
    """
    try:
        conn_string = config_manager.get_rds_connection_string(api_stage)
        conn = psycopg2.connect(conn_string)
        logger.debug("Connection to RDS Postgres instance succeeded")
        return conn
    except Exception as e:
        logger.error(f"ERROR: Could not connect to Postgres instance: {e}")
        raise


def get_db_conn_ssh(api_stage: str, tunnel: SSHTunnelForwarder) -> psycopg2.extensions.connection:
    """
    Connect to database via SSH tunnel.
    
    @param api_stage: Stage name
    @param tunnel: SSH tunnel instance
    @return: Database connection
    @raises: psycopg2.Error if connection fails
    """
    try:
        tunnel.start()
        tunnel.daemon_forward_servers = True
        
        ssh_db_creds = config_manager.get_ssh_db_credentials()
        
        conn = psycopg2.connect(
            database=ssh_db_creds['database'],
            user=ssh_db_creds['user'],
            password=ssh_db_creds['password'],
            host=tunnel.local_bind_host,
            port=tunnel.local_bind_port,
        )
        logger.debug("Connection to SSH database succeeded")
        return conn
    except Exception as e:
        logger.error(f"ERROR: Could not connect via SSH tunnel: {e}")
        raise


def get_db_data(cursor: psycopg2.extensions.cursor, query: str, params: Tuple[Any, ...] = ()) -> List[Tuple]:
    """
    Execute a SELECT query and return results.
    
    @param cursor: Database cursor
    @param query: SQL query with %s placeholders for parameters
    @param params: Query parameters (tuple)
    @return: List of tuples containing query results
    @raises: psycopg2.Error if query execution fails
    """
    try:
        logger.debug(f"Executing query: {query} with params: {params}")
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"ERROR executing query: {e}")
        raise


def missing_parameters(required_keys: List[str], event: Dict[str, Any]) -> List[str]:
    """
    Find missing required parameters in event.
    
    @param required_keys: List of required parameter keys
    @param event: Event dictionary
    @return: List of missing parameter names
    """
    return [key for key in required_keys if key not in event]


def get_cur_cashbal(account_id: str, cursor: psycopg2.extensions.cursor) -> Optional[Tuple]:
    """
    Get current cash balance for an account.
    
    @param account_id: Account ID
    @param cursor: Database cursor
    @return: Tuple with cash balance or None
    @raises: psycopg2.Error if query execution fails
    """
    query = "SELECT cash_balance FROM public.ledger_history WHERE account_id = %s ORDER BY rec_created_datetime DESC LIMIT 1"
    try:
        logger.debug(f"Getting cash balance for account: {account_id}")
        cursor.execute(query, (account_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"ERROR getting cash balance: {e}")
        raise


def ins_order_history(account_id: str, amount: Any, coid: str, conid: int, cur: psycopg2.extensions.cursor,
                      option_expiry_date: int, option_strike: float, option_type: str, ordertype: str,
                      parentid: str, price: float, quantity: float, quote_timestamp: str,
                      rec_created_by: str, sectype: str, side: str, ticker: str) -> Tuple[Optional[Tuple], str]:
    """
    Insert order into order_history table.
    
    @param account_id: Account ID
    @param amount: Order amount
    @param coid: Client Order ID
    @param conid: Contract ID
    @param cur: Database cursor
    @param option_expiry_date: Option expiry date (if applicable)
    @param option_strike: Option strike price (if applicable)
    @param option_type: Option type - C/P/N/A
    @param ordertype: Order type
    @param parentid: Parent order ID
    @param price: Price per unit
    @param quantity: Quantity
    @param quote_timestamp: Quote timestamp
    @param rec_created_by: Record created by
    @param sectype: Security type (STK/OPT)
    @param side: Order side (BUY/SELL)
    @param ticker: Ticker symbol
    @return: Tuple of (order_id, query_string) or (None, query_string)
    @raises: psycopg2.Error if query execution fails
    """
    query = """
        INSERT INTO public.order_history
        (account_id, conid, sectype, quantity, avg_price, side, ordertype, 
         option_type, option_expiry_date, ticker, option_strike, coid, parentid,
         quote_timestamp, rec_created_by, rec_created_datetime)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss'), %s, current_timestamp)
        RETURNING id
    """
    
    try:
        logger.debug(f"Inserting order for account {account_id}, conid {conid}")
        cur.execute(query, (
            account_id, conid, sectype, quantity, price, side, ordertype,
            option_type, option_expiry_date, ticker, option_strike, coid, parentid,
            quote_timestamp, rec_created_by
        ))
        result = cur.fetchone()
        logger.debug(f"Order inserted with ID: {result[0] if result else None}")
        return result, query
    except Exception as e:
        logger.error(f"ERROR inserting order history: {e}")
        raise


def ins_ledger_history(account_id: str, amount: Any, cur: psycopg2.extensions.cursor,
                       cur_cash_balance: float, order_id: int, quote_timestamp: str,
                       rec_created_by: str) -> Tuple[Optional[int], str]:
    """
    Insert ledger entry for transaction.
    
    @param account_id: Account ID
    @param amount: Transaction amount
    @param cur: Database cursor
    @param cur_cash_balance: Current cash balance after transaction
    @param order_id: Order ID
    @param quote_timestamp: Quote timestamp
    @param rec_created_by: Record created by
    @return: Tuple of (ledger_id, query_string) or (None, query_string)
    @raises: psycopg2.Error if query execution fails
    """
    query = """
        INSERT INTO public.ledger_history
        (account_id, order_id, transaction_amount, cash_balance, quote_timestamp,
         rec_created_by, rec_created_datetime)
        VALUES (%s, %s, %s, %s, to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss'),
                %s, current_timestamp)
        RETURNING id
    """
    
    try:
        logger.debug(f"Inserting ledger entry for account {account_id}")
        cur.execute(query, (
            account_id, order_id, amount, cur_cash_balance,
            quote_timestamp, rec_created_by
        ))
        result = cur.fetchone()
        logger.debug(f"Ledger entry inserted with ID: {result[0] if result else None}")
        return (result[0] if result else None, query)
    except Exception as e:
        logger.error(f"ERROR inserting ledger history: {e}")
        raise


