import psycopg2 as psycopg2
import os
from chalicelib.setup_logger import get_logger
from configparser import ConfigParser
from sshtunnel import SSHTunnelForwarder

logger = get_logger(__name__)
_config_file = os.path.join(
    os.path.dirname(__file__), 'config.ini')


def _readConfig():
    parser = ConfigParser()
    parser.read(_config_file)
    return parser


def _getRDSConnString(api_stage: str) -> str:
    cfg = _readConfig()
    required_keys = ['RDS_HOST', 'RDS_USERNAME', 'RDS_USER_PWD', 'RDS_DB_NAME']

    missing_params = missing_parameters(required_keys, cfg[api_stage])
    if missing_params:
        raise Exception("Missing Keys in configuration" + ", ".join(missing_params))

    # rds settings
    rds_host = cfg[api_stage]['RDS_HOST']
    rds_username = cfg[api_stage]['RDS_USERNAME']
    rds_user_pwd = cfg[api_stage]['RDS_USER_PWD']
    rds_db_name = cfg[api_stage]['RDS_DB_NAME']
    conn_string = "host=%s user=%s password=%s dbname=%s" % \
                  (rds_host, rds_username, rds_user_pwd, rds_db_name)
    logger.debug(f"Credentials: {rds_host} {rds_username} {rds_db_name}")
    return conn_string


def getDBConn(api_stage: str, tunnel: SSHTunnelForwarder = None) -> object:
    # use plain db connection if executed on aws , identified by stage = dev
    if api_stage.upper() == 'DEV':
        conn = getDBConn_rds(api_stage)
    else:
        # use plain ssh tunnel to connect if executed on local , identified by stage = local
        conn = getDBConn_ssh(api_stage, tunnel)
    return conn


def getDBConn_rds(api_stage: str) -> psycopg2.connect:
    """
        This method connects to back testing DB directly.

        @param api_stage: stage name from API gateway used to lookup DB credentials from config.ini
                          The stage name is created in the API gateway integration request section
        @return:
        """
    conn_string = _getRDSConnString(api_stage)
    try:
        conn = psycopg2.connect(conn_string)
    except Exception as e:
        logger.error("ERROR: Could not connect to Postgres instance.")
        logger.error(e)
    logger.debug("Connection to RDS Postgres instance succeeded")
    return conn


def getDBConn_ssh(api_stage: str, tunnel: SSHTunnelForwarder) -> psycopg2.connect:
    """
    This method connects to back testing DB via ssh.

    :param api_stage: stage name from API gateway used to lookup DB credentials from config.ini
                      The stage name is created in the API gateway integration request section

    :param tunnel: SSHTunnelForwarder object
    :return:

    """
    # Start the tunnel
    tunnel.start()
    tunnel.daemon_forward_servers = True
    # Create a database connection
    conn = psycopg2.connect(
        database='GKBackTesting1',
        user='postgres',
        password='nanbandev_123',
        host=tunnel.local_bind_host,
        port=tunnel.local_bind_port,
    )
    return conn


def missing_parameters(req_keys: list, event: dict) -> list:
    """

    @rtype: object
    """
    missing_params = []
    # raise error if necessary fields are not available.
    for key in req_keys:
        if key not in event:
            missing_params.append(key)
    return missing_params


def get_db_data(conn_db: getDBConn, query_str: str) -> list:
    try:
        with conn_db as cur:
            cur.execute(query_str)
            dbrows = cur.fetchall()
            logger.debug("output: " + str(dbrows))
    except Exception as e:
        logger.error(e)
        raise Exception(f"Error executing Query in DB: {query_str}")
    return dbrows


def get_cur_cashbal(account_id, cur):
    # get previous cash balance
    query_str = f"""
                    select a.cashbalance 
                      from public.sim_ledger_history a
                    where a.account_id = '{account_id}'
                      and a.rec_created_datetime = (select max(rec_created_datetime) 
                                                    from public.sim_ledger_history b
                                                    where b.account_id = a.account_id);
                            """
    logger.debug("query: {}".format(query_str))
    cur.execute(query_str)
    prev_cash_bal_tup = cur.fetchone()
    return prev_cash_bal_tup


def ins_ledger_history(account_id, amount, cur, cur_cash_balance, order_id, quote_timestamp,
                        rec_created_by):
    query_str = f"""
             insert into public.sim_ledger_history
                 (account_id, cashbalance, order_id, order_amount, quote_timestamp, rec_created_by)
                 values
                 ('{account_id}', {cur_cash_balance}, {order_id}, {amount}, 
                    to_timestamp('{quote_timestamp}','yyyy-mm-dd hh24:mi:ss'),
                    '{rec_created_by}')
                 returning ledger_id;
            """
    logger.debug("query: {}".format(query_str))
    cur.execute(query_str)
    ledger_id = cur.fetchone()[0]
    return ledger_id, query_str


def ins_order_history(account_id, amount, coid, conid, cur, option_expiry_date, option_strike,
                       option_type, ordertype, parentid, price, quantity, quote_timestamp,
                       rec_created_by, sectype, side, ticker):
    query_str = f"""INSERT INTO public.sim_order_history 
                                    (account_id, conid, option_type, option_expiry_date, option_strike, 
                                    coid, parentid, 
                                    ordertype, price, side, 
                                    ticker, sectype, quantity, amount, quote_timestamp, rec_created_by)
                                VALUES('{account_id}', {conid}, '{option_type}', {option_expiry_date},
                                        {option_strike},'{coid}', 
                                        '{parentid}', '{ordertype}', {price}, 
                                        '{side}', '{ticker}', '{sectype}', {quantity}, {amount},
                                        to_timestamp('{quote_timestamp}','yyyy-mm-dd hh24:mi:ss'),
                                        '{rec_created_by}')
                                returning order_id;
                                """
    logger.debug("query: {}".format(query_str))
    cur.execute(query_str)
    order_id_tup = cur.fetchone()
    return order_id_tup, query_str


if __name__ == "__main__":
    logger.setLevel('DEBUG')
    print(_getRDSConnString('dev'))
