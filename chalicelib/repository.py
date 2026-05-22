import decimal
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from chalicelib import utils
from chalicelib.setup_logger import get_logger
from chalicelib.config import config_manager
from chalicelib import constants
from sshtunnel import SSHTunnelForwarder
import psycopg2

logger = get_logger(__name__)


class PortalDB:
    """Context manager for database operations."""
    
    def __init__(self, api_stage: str):
        """
        Initialize PortalDB with API stage.
        
        @param api_stage: Stage name (LOCAL, DEV, PROD)
        """
        self.api_stage = api_stage
        self.conn = None
        self.tunnel = None

    def __enter__(self) -> 'PortalDB':
        """Enter context manager and establish database connection."""
        try:
            if self.api_stage.upper() != 'LOCAL':
                self.conn = utils.get_db_conn(self.api_stage)
            else:
                # Create SSH tunnel for local development
                ssh_config = config_manager.get_ssh_config()
                self.tunnel = SSHTunnelForwarder(
                    (ssh_config['ssh_host'], 22),
                    ssh_username=ssh_config['ssh_username'],
                    ssh_private_key=ssh_config['ssh_key_path'],
                    remote_bind_address=(ssh_config['remote_bind_address'], ssh_config['remote_bind_port']),
                    local_bind_address=(ssh_config['local_bind_address'], ssh_config['local_bind_port'])
                )
                self.conn = utils.get_db_conn(self.api_stage, self.tunnel)
            return self
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close connections."""
        try:
            if self.conn:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
                self.conn.close()
            if self.tunnel and self.api_stage.upper() == 'LOCAL':
                self.tunnel.stop()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

    def get_strikes(self, conid: int, month: str) -> List[Tuple]:
        """
        Return records for strikes of all call and put options for a specified month.
        
        @param conid: SPY contract id
        @param month: month of the year to look up all the strikes available
        @return: List of tuples with (option_type, strike)
        @raises: psycopg2.Error if query execution fails
        """
        query = """
            SELECT option_type, strike::varchar(255) 
            FROM public.sim_strikes 
            WHERE conid = %s AND option_month = %s
        """
        return utils.get_db_data(self.conn.cursor(), query, (conid, month))

    def get_info(self, conid: int, month: str, option_type: str, strike: str) -> List[Tuple]:
        """
        Return option contract information for a specific strike price.
        
        @param conid: Contract id
        @param month: Option month
        @param option_type: Option type (C/P)
        @param strike: Strike price
        @return: List of tuples with option contract details
        @raises: psycopg2.Error if query execution fails
        """
        query = """
            SELECT contractid as conid, 
                   ltrim(to_char(strike,'9999999999')) as astrike, 
                   option_type as right, 
                   option_expiry_date as maturityDate
            FROM public.sim_contracts 
            WHERE conid = %s 
              AND option_month = %s
              AND option_type = %s
              AND strike = %s
        """
        return utils.get_db_data(self.conn.cursor(), query, (conid, month, option_type, strike))

    def get_snapshot(self, conids: str, fields: str, quotetime: str) -> List[Tuple]:
        """
        Return quotes for the specified contract IDs.
        
        @param conids: List of conids separated by comma
        @param fields: List of fields separated by comma (31, 84, 86)
        @param quotetime: Quote timestamp in format 'YYYY-MM-DD HH:MM:SS'
        @return: List of tuples with quote data
        @raises: psycopg2.Error if query execution fails
        """
        try:
            if fields == constants.FIELD_CURRENT_PRICE:
                query = """
                    SELECT DISTINCT conid, last_price::varchar(25)
                    FROM public.sim_stock_history
                    WHERE conid = %s
                      AND quote_datetime=to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss')
                """
                # Note: conids in query is treated as a single value
                return utils.get_db_data(self.conn.cursor(), query, (conids, quotetime))
                
            elif fields == constants.FIELD_BID_ASK:
                query = """
                    SELECT DISTINCT contractid, bid_price::varchar(25), ask_price::varchar(25)
                    FROM public.sim_option_history
                    WHERE contractid = %s
                      AND quote_datetime=to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss')
                """
                return utils.get_db_data(self.conn.cursor(), query, (conids, quotetime))
            else:
                raise ValueError(f"Invalid fields parameter: {fields}. Only '31' or '84,86' allowed")
        except Exception as e:
            logger.error(f"ERROR in get_snapshot: {e}")
            raise

    def put_order(self, account_id: str, conid: int, coid: str, parentid: str, ordertype: str, 
                  price: float, side: str, ticker: str, sectype: str, quantity: float, 
                  quote_timestamp: str) -> List[Dict[str, Any]]:
        """
        Place an order and update ledger and positions.
        
        @param account_id: Account ID
        @param conid: Contract ID
        @param coid: Client Order ID
        @param parentid: Parent Order ID
        @param ordertype: Order type (LIMIT, MARKET, etc.)
        @param price: Price per unit
        @param side: Order side (BUY/SELL)
        @param ticker: Ticker symbol
        @param sectype: Security type (STK/OPT)
        @param quantity: Order quantity
        @param quote_timestamp: Quote timestamp
        @return: List with order details or error message
        """
        rec_created_by = 'ORDER API'
        
        try:
            with self.conn.cursor() as cur:
                # Get contract details for options
                if sectype == constants.SECTYPE_OPTION:
                    amount = Decimal(price * 100 * quantity)
                    query = """
                        SELECT option_expiry_date, strike, option_type
                        FROM public.sim_contracts 
                        WHERE contractid = %s
                    """
                    cur.execute(query, (conid,))
                    res_tup = cur.fetchone()
                    
                    if res_tup is None:
                        return [{"application error": constants.ERROR_CONTRACT_NOT_FOUND}]
                    
                    option_expiry_date = res_tup[0]
                    option_strike = res_tup[1]
                    option_type = res_tup[2]
                else:
                    # Stock order
                    option_expiry_date = constants.DEFAULT_OPTION_EXPIRY_DATE
                    option_strike = constants.DEFAULT_OPTION_STRIKE
                    option_type = constants.DEFAULT_OPTION_TYPE
                    amount = Decimal(price * quantity)

                logger.debug(f"option_expiry_date: {option_expiry_date}, option_strike: {option_strike}, "
                            f"option_type: {option_type}, amount: {amount}")

                # Get current cash balance
                prev_cash_bal_tup = utils.get_cur_cashbal(account_id, cur)
                
                if prev_cash_bal_tup is None:
                    return [{"app error": constants.ERROR_NO_BALANCE.format(account_id=account_id)}]
                
                prev_cash_balance = prev_cash_bal_tup[0]
                logger.debug(f"Prev cashbalance: {prev_cash_balance}")

                # Calculate new cash balance based on order side
                if side.upper() == constants.ORDER_TYPE_BUY:
                    amount = amount * -1
                elif side.upper() == constants.ORDER_TYPE_SELL:
                    quantity = quantity * -1
                else:
                    raise ValueError(constants.ERROR_INVALID_ORDER_SIDE)

                cur_cash_balance = prev_cash_balance + amount
                
                if cur_cash_balance <= 0:
                    raise ValueError(constants.ERROR_NEGATIVE_BALANCE.format(amount=amount))

                # Check positions to avoid naked sells
                query = """
                    SELECT quantity FROM public.sim_positions
                    WHERE account_id = %s AND conid = %s
                """
                cur.execute(query, (account_id, conid))
                cur_position = cur.fetchone()

                if (side.upper() == constants.ORDER_TYPE_SELL and
                    sectype.upper() == constants.SECTYPE_STOCK and
                    cur_position is None):
                    return [{"application error": constants.ERROR_INSUFFICIENT_POSITIONS.format(quantity=quantity)}]

                # Insert order history
                order_id_tup, _ = utils.ins_order_history(
                    account_id=account_id, amount=amount, coid=coid, conid=conid, cur=cur,
                    option_expiry_date=option_expiry_date, option_strike=option_strike,
                    option_type=option_type, ordertype=ordertype, parentid=parentid,
                    price=price, quantity=quantity, quote_timestamp=quote_timestamp,
                    rec_created_by=rec_created_by, sectype=sectype, side=side, ticker=ticker
                )
                
                if order_id_tup is None:
                    raise ValueError(constants.ERROR_UNABLE_TO_INSERT_ORDER)
                
                order_id = order_id_tup[0]
                logger.debug(f"order_id: {order_id}")

                # Insert ledger history
                ledger_id, _ = utils.ins_ledger_history(
                    account_id=account_id, amount=amount, cur=cur,
                    cur_cash_balance=cur_cash_balance, order_id=order_id,
                    quote_timestamp=quote_timestamp, rec_created_by=rec_created_by
                )
                logger.debug(f"ledger_id: {ledger_id}")

                # Insert/update positions
                query = """
                    INSERT INTO public.sim_positions
                    (account_id, conid, sectype, quantity, avg_price, side, ordertype, option_type, 
                     option_expiry_date, ticker, option_strike, rec_created_by) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (account_id, conid) DO UPDATE
                        SET 
                            quantity = sim_positions.quantity + EXCLUDED.quantity,
                            side = CASE WHEN sim_positions.side = 'SELL' 
                                        THEN EXCLUDED.side 
                                        ELSE sim_positions.side END,
                            rec_updated_datetime = current_timestamp,
                            rec_created_by = CASE 
                                WHEN sim_positions.side = 'BUY' AND sim_positions.sectype = 'OPT'
                                    THEN EXCLUDED.rec_created_by || ' - Collect Juice'
                                WHEN sim_positions.side = 'SELL' AND sim_positions.sectype = 'OPT'
                                    THEN EXCLUDED.rec_created_by || ' - Buy Back 5% or 25% credit'
                                ELSE EXCLUDED.rec_created_by
                            END
                """
                cur.execute(query, (
                    account_id, conid, sectype, quantity, price, side, ordertype,
                    option_type, option_expiry_date, ticker, option_strike, rec_created_by
                ))
                logger.debug(f"Position updated: {cur.statusmessage}")

                return [{'order_id': order_id, 'local_order_id': coid, 'order_status': 'Filled'}]

        except (ValueError, psycopg2.Error) as e:
            logger.error(f"Error in put_order: {e}")
            self.conn.rollback()
            return [{'handled_exception': str(e)}]
        except Exception as e:
            logger.error(f"Unexpected error in put_order: {e}")
            self.conn.rollback()
            return [{'handled_exception': str(e)}]

    def get_ledger(self, account_id: str, quotetime: str) -> List[Tuple]:
        """
        Get cash balance and net liquidation value for an account.
        
        @param account_id: Account ID
        @param quotetime: Quote timestamp
        @return: List of tuples with (balance_amount, balance_type)
        @raises: psycopg2.Error if query execution fails
        """
        try:
            # Get current cash balance
            query = """
                SELECT a.cashbalance, 'cashbalance' as bal_type
                FROM public.sim_ledger_history a
                WHERE a.account_id = %s
                  AND a.rec_created_datetime = (
                      SELECT MAX(rec_created_datetime) 
                      FROM public.sim_ledger_history b
                      WHERE b.account_id = a.account_id
                  )
                UNION
                SELECT SUM(cur_liq), 'netliquidationvalue' as bal_type 
                FROM (
                    SELECT
                        account_id as acctId,
                        ((CASE WHEN UPPER(side) = 'SELL' THEN -1 ELSE 1 END) * 
                         quantity * z.last_price)::float as cur_liq
                    FROM public.sim_positions a
                    LEFT JOIN public.sim_option_history z ON
                        z.contractid = a.conid
                        AND z.quote_datetime = to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss')
                    WHERE a.account_id = %s
                      AND sectype = 'OPT'
                    UNION 
                    SELECT
                        account_id as acctId,
                        (quantity * COALESCE(z.last_price, 0))::float as cur_liq
                    FROM public.sim_positions a
                    LEFT JOIN public.sim_stock_history z ON
                        z.conid = a.conid
                        AND z.quote_datetime = to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss')
                    WHERE a.account_id = %s
                      AND sectype = 'STK'
                ) z
                GROUP BY acctId
            """
            return utils.get_db_data(self.conn.cursor(), query, (account_id, quotetime, account_id, quotetime, account_id))
        except Exception as e:
            logger.error(f"ERROR in get_ledger: {e}")
            raise

    def get_positions(self, account_id: str, quotetime: str) -> List[Tuple]:
        """
        Get all open positions for an account.
        
        @param account_id: Account ID
        @param quotetime: Quote timestamp
        @return: List of tuples with position details
        @raises: psycopg2.Error if query execution fails
        """
        try:
            query = """
                SELECT
                    account_id as acctId,
                    a.conid::varchar(25),
                    ticker,
                    sectype as assetClass,
                    quantity as position,
                    a.option_type as putOrCall,
                    side as right,
                    a.option_expiry_date::varchar(25) as expiry,
                    option_strike as strike,
                    expired,
                    rec_created_datetime::varchar(25),
                    rec_updated_datetime::varchar(25),
                    rec_created_by,
                    z.last_price::float as mktPrice,
                    avg_price::float as avgPrice
                FROM public.sim_positions a
                LEFT JOIN public.sim_option_history z ON
                    z.contractid = a.conid
                    AND z.quote_datetime = to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss')
                WHERE a.account_id = %s
            """
            return utils.get_db_data(self.conn.cursor(), query, (quotetime, account_id))
        except Exception as e:
            logger.error(f"ERROR in get_positions: {e}")
            raise

    def post_settlement(self, account_id: str, quotetime: str) -> List[Dict[str, Any]]:
        """
        Settle open positions at the end of day.
        
        @param account_id: Account ID
        @param quotetime: Quote timestamp (typically EOD)
        @return: List with settlement status or error
        """
        rec_created_by = 'SETTLEMENT API'
        spy_con_id = constants.SPY_CON_ID
        settle_date = quotetime.split(' ')[0].replace('-', '')

        try:
            with self.conn.cursor() as cur:
                # Get open positions to settle
                query = """
                    SELECT account_id, conid, ticker, sectype,
                           quantity, option_type, side, option_expiry_date, 
                           option_strike, expired 
                    FROM public.sim_positions 
                    WHERE account_id = %s 
                      AND option_expiry_date = %s
                      AND side = 'SELL'
                """
                cur.execute(query, (account_id, int(settle_date)))
                tups = cur.fetchall()

                if len(tups) == 0:
                    self._delete_expired_positions(account_id, cur, int(settle_date))
                    return [{"settlement status": "No positions to settle"}]

                if len(tups) > 1:
                    logger.error(f"Multiple obligations found: {tups}")
                    raise ValueError("Cannot have more than one SELL obligation")

                # Process single obligation
                for row in tups:
                    option_data = {
                        'quantity': row[4],
                        'option_type': row[5],
                        'option_strike': row[8],
                        'ticker': row[2],
                        'side': row[6],
                        'sectype': row[3]
                    }

                # Get current cash balance
                prev_cash_bal_tup = utils.get_cur_cashbal(account_id, cur)
                if prev_cash_bal_tup is None:
                    return [{"app error": constants.ERROR_NO_BALANCE.format(account_id=account_id)}]
                
                prev_cash_balance = prev_cash_bal_tup[0]
                logger.debug(f"Previous cash balance: {prev_cash_balance}")

                # Check for existing stock positions
                query = """
                    SELECT account_id, conid, ticker, sectype,
                           quantity, option_type, side, option_expiry_date, 
                           option_strike, expired 
                    FROM public.sim_positions 
                    WHERE account_id = %s AND sectype = 'STK'
                """
                cur.execute(query, (account_id,))
                stk_tups = cur.fetchall()
                stk_avail_ind = len(stk_tups) == 1

                # Get EOD stock price
                query = """
                    SELECT MAX(last_price) 
                    FROM public.sim_stock_history 
                    WHERE quote_datetime = to_timestamp(%s, 'yyyy-mm-dd hh24:mi:ss')
                      AND conid = %s
                """
                cur.execute(query, (quotetime, spy_con_id))
                stk_eod_price_tup = cur.fetchone()
                
                if not stk_eod_price_tup or not stk_eod_price_tup[0]:
                    raise ValueError(f"EOD price for SPY not available for {quotetime}")
                
                stk_eod_price = stk_eod_price_tup[0]
                
                # Determine if option is in-the-money
                is_in_the_money = (
                    (option_data['option_type'] == 'P' and stk_eod_price <= option_data['option_strike']) or
                    (option_data['option_type'] == 'C' and stk_eod_price >= option_data['option_strike'])
                )

                logger.debug(f"Option type: {option_data['option_type']}, Strike: {option_data['option_strike']}, "
                            f"EOD Price: {stk_eod_price}, ITM: {is_in_the_money}")

                # Determine settlement actions
                buy_stk_ind = (option_data['side'] == 'SELL' and option_data['option_type'] == 'P' and is_in_the_money)
                sell_stk_ind = (option_data['side'] == 'SELL' and option_data['option_type'] == 'C' and stk_avail_ind and is_in_the_money)

                if buy_stk_ind or sell_stk_ind:
                    self._process_settlement_scenario(
                        cur, account_id, option_data, prev_cash_balance, stk_eod_price,
                        quotetime, rec_created_by, spy_con_id, buy_stk_ind, sell_stk_ind
                    )

                self._delete_expired_positions(account_id, cur, int(settle_date))
                return [{"settlement status": f"Positions settled for {settle_date} at {quotetime}"}]

        except (ValueError, psycopg2.Error) as e:
            logger.error(f"Error in post_settlement: {e}")
            self.conn.rollback()
            return [{'handled_exception': str(e)}]
        except Exception as e:
            logger.error(f"Unexpected error in post_settlement: {e}")
            self.conn.rollback()
            return [{'handled_exception': str(e)}]

    def _process_settlement_scenario(self, cur: psycopg2.extensions.cursor, account_id: str, 
                                     option_data: Dict[str, Any], prev_cash_balance: float,
                                     stk_eod_price: float, quotetime: str, rec_created_by: str,
                                     spy_con_id: int, buy_stk_ind: bool, sell_stk_ind: bool) -> None:
        """
        Process settlement based on whether to buy or sell stock.
        
        @param cur: Database cursor
        @param account_id: Account ID
        @param option_data: Option data dictionary
        @param prev_cash_balance: Previous cash balance
        @param stk_eod_price: Stock EOD price
        @param quotetime: Quote timestamp
        @param rec_created_by: Record creator
        @param spy_con_id: SPY contract ID
        @param buy_stk_ind: Whether to buy stock
        @param sell_stk_ind: Whether to sell stock
        """
        settle_amount = Decimal(0)
        settle_qnty = 0
        side = ''
        next_cash_bal = float(prev_cash_balance)

        if buy_stk_ind:
            settle_qnty = option_data['quantity'] * -100
            settle_amount = (option_data['option_strike'] * settle_qnty) * -1
            side = 'BUY'
            next_cash_bal = float(prev_cash_balance) + float(settle_amount)

            if settle_qnty > 0:
                query = """
                    INSERT INTO public.sim_positions 
                    (account_id, conid, sectype, quantity, avg_price, side, ordertype, 
                     option_expiry_date, ticker, option_strike, rec_created_by) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (account_id, conid) DO UPDATE
                        SET quantity = sim_positions.quantity + EXCLUDED.quantity, 
                            avg_price = EXCLUDED.avg_price,
                            rec_created_by = 'Settlement API - Added to existing stks'
                """
                cur.execute(query, (
                    account_id, spy_con_id, 'STK', settle_qnty, option_data['option_strike'],
                    side, 'LIMIT', -999, option_data['ticker'], option_data['option_strike'], rec_created_by
                ))
                logger.debug(f"Position inserted: {cur.statusmessage}")

        elif sell_stk_ind:
            settle_qnty = option_data['quantity'] * 100
            settle_amount = (option_data['option_strike'] * settle_qnty) * -1
            side = 'SELL'
            next_cash_bal = float(prev_cash_balance) + float(settle_amount)

            # Update stock positions
            query = """
                UPDATE public.sim_positions 
                SET quantity = quantity + %s
                WHERE account_id = %s AND conid = %s AND sectype = %s AND ticker = %s
            """
            cur.execute(query, (settle_qnty, account_id, spy_con_id, 'STK', option_data['ticker']))
            logger.debug(f"Position updated: {cur.statusmessage}")

            # Delete zero quantity positions
            query = """
                DELETE FROM public.sim_positions 
                WHERE account_id = %s AND conid = %s AND sectype = %s 
                  AND ticker = %s AND quantity = 0
            """
            cur.execute(query, (account_id, spy_con_id, 'STK', option_data['ticker']))
            logger.debug(f"Zero positions deleted: {cur.statusmessage}")

        # Insert order history for settlement
        order_id_tup, _ = utils.ins_order_history(
            account_id=account_id, amount=Decimal(settle_amount), coid='stlmnt_coid',
            conid=spy_con_id, cur=cur, option_expiry_date=-999, option_strike=-999,
            option_type='N/A', ordertype='LIMIT', parentid='parent_stlmnt_coid',
            price=option_data['option_strike'], quantity=settle_qnty,
            quote_timestamp=quotetime, rec_created_by=rec_created_by,
            sectype='STK', side=side, ticker=option_data['ticker']
        )

        if order_id_tup:
            order_id = order_id_tup[0]
            utils.ins_ledger_history(
                account_id=account_id, amount=Decimal(settle_amount), cur=cur,
                cur_cash_balance=next_cash_bal, order_id=order_id,
                quote_timestamp=quotetime, rec_created_by=rec_created_by
            )

    def _delete_expired_positions(self, account_id: str, cur: psycopg2.extensions.cursor, 
                                   settle_date: int) -> None:
        """
        Delete expired option positions.
        
        @param account_id: Account ID
        @param cur: Database cursor
        @param settle_date: Settlement date
        """
        query = """
            DELETE FROM public.sim_positions 
            WHERE account_id = %s AND option_expiry_date = %s
        """
        cur.execute(query, (account_id, settle_date))
        logger.debug(f"Expired positions deleted: {cur.statusmessage}")


if __name__ == "__main__":
    logger.setLevel('DEBUG')
    output = None
    # Example usage (commented out):
    # with PortalDB('local') as portal_db:
    #     output = portal_db.get_strikes(756733, 'DEC15')
    #     output = portal_db.get_info(756733, 'JAN11', 'C', '114')
    #     output = portal_db.get_snapshot('756733', '31', '2014-08-04 12:15:00')
    #     output = portal_db.put_order(
    #         account_id='DU2387565', conid=756733, coid='testLocalOrd:STK1',
    #         parentid='testLocalOrd:STKP11', ordertype='LIMIT', price=290,
    #         side='BUY', ticker='SPY', sectype='STK', quantity=600,
    #         quote_timestamp='2013-06-28 13:30:00'
    #     )
    #     output = portal_db.get_ledger(account_id='gkbot1M-81516', quotetime='2016-10-14 22:15:00')
    #     output = portal_db.get_positions(account_id='mano1M-1', quotetime='2015-09-11 16:00:00')
    #     output = portal_db.post_settlement(account_id='stk4-ec2-1s', quotetime='2016-01-22 16:15:00')
    # 
    # print(output)
