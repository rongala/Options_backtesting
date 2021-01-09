import decimal
from chalicelib import utils as utils
from chalicelib.setup_logger import get_logger
from sshtunnel import SSHTunnelForwarder

logger = get_logger(__name__)


class PortalDB:
    def __init__(self, api_stage):
        self.api_stage = api_stage

    def __enter__(self):
        if self.api_stage.upper() != 'LOCAL':
            self.conn = utils.getDBConn(self.api_stage)
        else:
            # creating tunnel instead of utility is to be able to close the tunnel with
            # scope of context manager.
            self.tunnel = SSHTunnelForwarder(
                ('ec2-54-190-122-132.us-west-2.compute.amazonaws.com', 22),
                ssh_username='ec2-user',
                ssh_private_key='/Users/rronga/Documents/work/nanban/nanban-dev-ec2.pem',
                remote_bind_address=('backtestingdb-cluster.cluster-cwm2blxcre5t.us-west-2.rds.amazonaws.com',
                                     5432),
                local_bind_address=('localhost', 6543)
            )
            self.conn = utils.getDBConn(self.api_stage, self.tunnel)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()
        if self.api_stage.upper() == 'LOCAL':
            self.tunnel.stop()

    def getStrikes(self, conid: int, month: str) -> list:
        """
        Return records for strikes of all call and put options for a specified month
        from back testing db.

        @param conid: SPY contract id
        @param month: month of the year to look up all the strikes available.

        sample input:
        -------------
            getStrikes(756733, 'DEC15')
        sample output :
        -------------
            [('P', '198.00'), ('C', '252.50'), ('P', '140.50'), ('C', '150.00')]
        """
        query = f"""select option_type, strike::varchar(255) from public.sim_strikes 
                where conid = {conid} and option_month = '{month}'
                ;
            """
        logger.debug("query: {}".format(query))
        return utils.get_db_data(self.conn.cursor(), query)

    def getinfo(self, conid: int, month: str, option_type: str, strike: str) -> list:
        """
        Return information about the option contract for a specific strike price.

        sample Input:
        -------------
            getConinfo('756733','DEC15','C','189')
        sample Output:
        -------------
            [('2015120410018900', '189', 'C', 20151204),
            ('2015120410018900', '189', 'C', 20151211),
            ('2015120410018900', '189', 'C', 20151218)]
        """
        query = f"""select contractid as conid, 
                  ltrim(to_char(strike,'9999999999')) as astrike, option_type as right, 
                  option_expiry_date as maturityDate
            from public.sim_contracts 
            where conid = {conid} 
            and option_month = '{month}'
            and option_type = '{option_type}'
            and strike = '{strike}';
            """
        logger.debug("query: {}".format(query))
        return utils.get_db_data(self.conn.cursor(), query)

    def getsnapshot(self, conids: str, fields: str, quotetime: str) -> list:
        """
        Return quotes for the conid specified

        @param conids:
                list of conids separated by comma. e.g. 2013062810011100
        @param fields:
                list of fields separated by comma. e.g. 31,84,86
                    31: current price
                    84: bid price
                    86: ask price
        @param quotetime: '2013-06-28 11:45:00'


        sample Input:
        -------------
            getsnapshot('756733','31','2014-08-04 12:15:00')
            getsnapshot('756733','84,86','2013-06-28 11:45:00')
        sample Output:
        --------------
            [('2015120410018900', '189', 'C', 20151204),
            ('2015120410018900', '189', 'C', 20151211),
            ('2015120410018900', '189', 'C', 20151218)]
        """
        if fields == '31':
            query = f"""select distinct conid, last_price::varchar(25)
                        from public.sim_stock_history
                        where conid in ({conids})
                        and quote_datetime=to_timestamp('{quotetime}','yyyy-mm-dd hh24:mi:ss')
            ;
            """
        elif fields == '84,86':
            query = f"""select distinct contractid, bid_price::varchar(25), ask_price::varchar(25)
                        from public.sim_option_history
                        where contractid in ({conids})
                        and quote_datetime=to_timestamp('{quotetime}','yyyy-mm-dd hh24:mi:ss');
                            """

        logger.debug("query: {}".format(query))
        return utils.get_db_data(self.conn.cursor(), query)

    def putorder(self, account_id: str, conid: int, coid: str, parentid: str, ordertype: str, price: float, side: str,
                 ticker: str, sectype: str, quantity: float, quote_timestamp: str) -> list:
        """

        When an order is placed, it is
        1) recorded in the order_history and
        2) the ledger_history is updated with the transaction amount.
        3) position is also created in the position table.

        @param account_id:
        @param conid: contract id of the STK SPY, or OPT CALL/PUT BUY/SELL of SPY
        @param coid:
        @param parentid:
        @param ordertype: BUY/SELL
        @param price:
        @param side: CALL/PUT
        @param ticker:
        @param sectype: STK/OPT
        @param quantity:
        @param quote_timestamp:
        @return:

        sample Input:
        -------------
            getPortalDB.putorder(
                account_id='DU2387565',
                conid=756733,
                coid='testLocalOrd:C1',
                parentid='testLocalOrd:P1',
                ordertype='STK',
                price=290,
                side='BUY',
                ticker='SPY',
                quantity=6,
                quote_timestamp='2013-06-28 13:30:00')

        sample Output:
        --------------
            [
                {
                    "order_id": 3,
                    "local_order_id": "DU2387565:C1",
                    "order_status": "Filled"
                }
            ]
        """
        # We need to handle multi sql transaction so we are not using _get_db_data method
        rec_created_by = 'ORDER API'
        try:
            with self.conn.cursor() as cur:
                # fetch the expiry Date to insert in to the ordrer history table.
                if sectype == 'OPT':
                    # if option order, multiply the quatity with 100 to make interms of lots.
                    amount = decimal.Decimal(price * 100 * quantity)
                    # fetch option expiry date if its an option order.
                    query_str = f"""select option_expiry_date, strike, option_type
                                    from public.sim_contracts 
                                    where contractid = {conid} """
                    logger.debug("query: {}".format(query_str))
                    cur.execute(query_str)
                    res_tup = cur.fetchone()
                    if res_tup is None:
                        return [{"application error": "Contract ID doesn't exist in Database"}]
                    option_expiry_date = res_tup[0]
                    option_strike = res_tup[1]
                    option_type = res_tup[2]
                else:
                    # when you buy stocks, there is no contract
                    option_expiry_date = -999
                    option_strike = -999
                    option_type = 'N/A'
                    amount = decimal.Decimal(price * quantity)
                logger.debug("option_expiry_date: " + str(option_expiry_date))
                logger.debug("option_strike: " + str(option_strike))
                logger.debug("option_type: " + option_type)
                logger.debug("amount: " + str(amount))

                # get current balance for the account
                prev_cash_bal_tup = utils.get_cur_cashbal(account_id, cur)

                if prev_cash_bal_tup is None:
                    return [{
                        "app error": f"No balance found for this account {account_id}. may be it is not seeded."}]
                prev_cash_balance = prev_cash_bal_tup[0]
                logger.debug("Prev cashbalance: " + str(prev_cash_balance))
                # Derive the current cash balance based on the order being placed.
                # for e.g. If its a buy then credit price*100, else deduct.
                # get_cur_bal = lambda lside, lprbal, lamt: lprbal - lamt \
                #     if lside.upper() == 'BUY' else lprbal + lamt

                if side.upper() == 'BUY':
                    amount = amount * -1
                elif side.upper() == 'SELL':
                    quantity = quantity * -1
                else:
                    raise Exception("Invalid order/opt side. It has to be either BUY or SELL")

                cur_cash_balance = prev_cash_balance + amount
                if cur_cash_balance <= 0:
                    raise Exception(f"This order causing -ve balance, deducting {amount}."
                                    f"NOTE: This error is not hanlded in IBKR API")

                # get positions to check to avoid naked sells of stk.
                query_str = f"""
                                select quantity from public.sim_positions
                                where account_id = '{account_id}'
                                  and conid = {conid};
                            """
                logger.debug("query: {}".format(query_str))
                cur.execute(query_str)
                cur_position = cur.fetchone()

                # plainly adding the quantity because it is *(-1) if sell order.
                # this logic avoids overselling the stocks. If positionas are available,
                # then adding order quantity to current position should be positive.
                # If there are no existing positions, then the current order quantity cannot be zero.
                if (
                        side.upper() == 'SELL' and sectype.upper() == 'STK'
                        and (((cur_position is None) and quantity < 0)
                             or
                             quantity < 0)
                ):
                    return [{"application error": f"Not enough positions to sell '{quantity}'"}]

                # ************************************************************************************************
                # insert record into order history table. get the order id and insert data into other tables.
                # ************************************************************************************************
                order_id_tup, query_str = utils.ins_order_history(account_id=account_id, amount=amount, coid=coid,
                                                                  conid=conid, cur=cur,
                                                                  option_expiry_date=option_expiry_date,
                                                                  option_strike=option_strike,
                                                                  option_type=option_type,
                                                                  ordertype=ordertype, parentid=parentid,
                                                                  price=price, quantity=quantity,
                                                                  quote_timestamp=quote_timestamp,
                                                                  rec_created_by=rec_created_by,
                                                                  sectype=sectype, side=side,
                                                                  ticker=ticker)
                if order_id_tup is None:
                    raise Exception("Unable to insert in to order history and create order id (series col)")
                order_id = order_id_tup[0]
                logger.debug("order_id: " + str(order_id))

                # **************************************
                # insert data into ledger history table
                # **************************************
                ledger_id, query_str = utils.ins_ledger_history(account_id=account_id, amount=amount, cur=cur,
                                                                cur_cash_balance=cur_cash_balance, order_id=order_id,
                                                                quote_timestamp=quote_timestamp,
                                                                rec_created_by=rec_created_by)
                logger.debug("ledger_id: " + str(ledger_id))

                # **************************************
                # Create positions based on the history
                # **************************************

                query_str = f"""
                 INSERT INTO public.sim_positions
                    (account_id, conid, sectype, quantity, avg_price, side, ordertype, option_type, 
                     option_expiry_date, ticker, option_strike, rec_created_by) 
                  VALUES 
                    ('{account_id}', '{conid}', '{sectype}', {quantity}, '{price}','{side}', '{ordertype}', '{option_type}', 
                      {option_expiry_date}, '{ticker}', {option_strike}, '{rec_created_by}') 
                    ON CONFLICT (account_id, conid) DO UPDATE
                        SET 
                            quantity = sim_positions.quantity + EXCLUDED.quantity,
                            side = case when (sim_positions.side = 'SELL') then EXCLUDED.side 
                                        else sim_positions.side end,
                            rec_updated_datetime = current_timestamp,
                            rec_created_by = case when (sim_positions.side = 'BUY' and sim_positions.sectype = 'OPT')
                                                    then EXCLUDED.rec_created_by || ' - Collect Juice'
                                                  when (sim_positions.side = 'SELL' and sim_positions.sectype = 'OPT')
                                                    then EXCLUDED.rec_created_by || ' - Buy Back 5% or 25% credit'
                                                  else EXCLUDED.rec_created_by
                                             end
                    ;
                """
                logger.debug("query: {}".format(query_str))
                cur.execute(query_str)
                # note cur.fetchone() will throw exceptio as "no results to fetch" for inserts. So using this method
                pos_insert_count = cur.statusmessage
                logger.debug("pos_insert_count: " + pos_insert_count)

        except Exception as e:
            logger.error(f"Error executing Query in DB: {query_str}")
            logger.error(e)
            self.conn.rollback()
            return [{'handled_exception': e.__str__()}]
            # sys.exit(1)
        return [{'order_id': order_id, 'local_order_id': coid, 'order_status': 'Filled'}]

    def getledger_bkp(self, account_id: str) -> list:
        """

        @param account_id:
        @return:

        sample Input:
        -------------
            getPortalDB.getledger(account_id='DU2387565')

        sample Output:
        --------------
            [('8570.00',)]
        """

        query = f"""select a.cashbalance 
                  from public.sim_ledger_history a
                where a.account_id = '{account_id}'
                  and a.rec_created_datetime = (select max(rec_created_datetime) 
                                                from public.sim_ledger_history b
                                                where b.account_id = a.account_id);
                    """
        logger.debug("query: {}".format(query))
        return utils.get_db_data(self.conn.cursor(), query)

    def getledger(self, account_id: str, quotetime: str) -> list:
        """

        :param account_id: string
        :param quotetime: string
        :return: list of tuples

        sample Input:
        -------------
            getPortalDB.getledger(account_id='DU2387565', quotetime = '2016-10-14 10:15')

        sample Output:
        --------------
            [(39394.0, 'cashbalance'), (2059248.82, 'netliquidationvalue')]
        """

        query = f"""select a.cashbalance, 'cashbalance' as bal_type
                      from public.sim_ledger_history a
                    where a.account_id = '{account_id}'
                      and a.rec_created_datetime = (select max(rec_created_datetime) 
                                                    from public.sim_ledger_history b
                                                    where b.account_id = a.account_id)
                    union
                    select sum(cur_liq), 'netliquidationvalue' as bal_type
                    from (
                        select
                            account_id as acctId,
                            ((case when upper(side) = 'SELL' 
                             then -1 
                             else 1 
                             end) * quantity * z.last_price)::float as cur_liq
                        from
                            public.sim_positions a
                        left join public.sim_option_history z on
                            z.contractid = a.conid
                            and z.quote_datetime = '{quotetime}'
                        where
                            account_id = '{account_id}'
                            and sectype = 'OPT'
                        union 
                        select
                            account_id as acctId,
                            (quantity * COALESCE(z.last_price,0))::float as cur_liq
                        from
                            public.sim_positions a
                        left join public.sim_stock_history z on
                            z.conid = a.conid
                            and z.quote_datetime = '{quotetime}'
                        where
                            account_id = '{account_id}'
                            and sectype = 'STK'
                        ) z
                    Group by acctId;
                    """
        logger.debug("query: {}".format(query))
        return utils.get_db_data(self.conn.cursor(), query)

    def getpositions(self, account_id: str, quotetime: str) -> list:
        """

        @param quotetime:
        @param account_id:
        @return: list of position records

        sample Input:
        -------------
            getPortalDB.getpositions(account_id='DU2387565',  quotetime = '2016-10-14 10:15)

        sample Output:
        --------------
            [
            ('DU2387565', '435098432', 'SPY', 'STK', '700', 'N/A', 'BUY', '-999', '-999.00', False,
                            '2020-09-21 23:37:07.07675', '2020-09-21 23:37:07.07675', 'ORDER API'),
            ('DU2387565', '2015120410019100', 'SPY', 'OPT', '-7', 'C', 'SELL', '20151204', '191.00', False,
                            '2020-09-21 23:37:11.19061', '2020-09-21 23:37:11.19061', 'ORDER API'),
            ('DU2387565', '2015120420019250', 'SPY', 'OPT', '7', 'P', 'BUY', '20151204', '112.00', False,
                            '2020-09-21 23:37:14.56719', '2020-09-21 23:37:44.19531', 'ORDER API')
            ]

        """

        query = f""" 
               select
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
                from
                    public.sim_positions a
                left join public.sim_option_history z on
                    z.contractid = a.conid
                    and z.quote_datetime = '{quotetime}'
                where
                    account_id = '{account_id}';
                """
        logger.debug("query: {}".format(query))
        return utils.get_db_data(self.conn.cursor(), query)

    def postsettlement(self, account_id: str, quotetime: str) -> list:
        """
        Settles the eod positions for a given account.
        Note: the qupte time must always be the 15:00:00 time of any day.

            1. get open positions, their strike and obligation (BUY/SELL) and option type (C/P)
            2. get the end of day spy price for that day in quote time.
            3. If in the money settle the position depending up on the obligation and option type.
                a. If Put Sold, that mean its L2, hence the process must acquire the stk.
                b. If Call sold, its L1, hence we must sell the stk.
            4. update the ledger_history (credit/Deduct based on the settlement)
            5. log in to order_history table (like selling or buying stk), to create an event trail.
            4. expire the rest of the open options.
            5. cleanup the zero positions.


        @param account_id:
        @param quotetime:
        @return:
        """

        rec_created_by = 'SETTLEMENT API'
        spy_con_id = 756733
        coid = 'stlmnt_coid'
        parent_stlmnt_coid = 'parent_stlmnt_coid'
        settle_order_type = 'LIMIT'
        not_applicable_num = -999
        not_applicable_str = 'N/A'
        sec_type = 'STK'
        try:
            settle_time = quotetime.split(' ')[1].split('.')[0]
            if settle_time != '16:15:00':
                return [{"App Error": "Settlement API can only be called at the end of the day. For. e.g. 19998-01-02 "
                                      "16:15:00"}]
            settle_date = quotetime.split(' ')[0].replace('-', '')

            with self.conn.cursor() as cur:
                ##############################################
                # get the current positions in to a dataframe.
                ##############################################
                query = f"""SELECT account_id, conid, ticker, sectype,
                                    quantity, option_type , side , option_expiry_date, 
                                    option_strike, expired 
                            FROM public.sim_positions 
                            WHERE account_id = '{account_id}' 
                            and option_expiry_date = {settle_date}
                            and side = 'SELL' ; 
                        """

                cur.execute(query)
                tups = cur.fetchall()

                if len(tups) == 0:
                    output = [{"settlement status": " No positions to settle"}]
                    logger.debug(output)
                    # delete the rest of the positions that do not have obligaton for the expiry data
                    self._delete_positions(account_id, cur, query, settle_date)
                    return output
                elif len(tups) > 1:
                    logger.error(tups)
                    raise Exception("Cannot have more than one SELL obligation")

                # print(tups)
                # it is assumed that accoutn will not have more than one obligation
                # if it has, it considered as exception and handled above.
                # so it is ok to accessing the variables in loop as it will execute only once.
                # sample db output:
                # ('DU2387565', 1998010520011000, 'SPY', 'OPT', -7, 'P', 'SELL', 19980105, Decimal('110.00'), False)
                for row in tups:
                    print(row)
                    df = {'quantity': row[4], 'option_type': row[5], 'option_strike': row[8], 'ticker': row[2],
                          'side': row[6], 'sectype': row[3]}
                    logger.debug(df.__str__())

                # get current balance for the account
                prev_cash_bal_tup = utils.get_cur_cashbal(account_id, cur)
                if prev_cash_bal_tup is None:
                    return [{
                        "app error": f"No balance found for this account {account_id}. may be it is not seeded."}]
                prev_cash_balance = prev_cash_bal_tup[0]
                logger.debug("Prev cashbalance: " + str(prev_cash_balance))

                # check positions if STK exists
                query = f"""SELECT account_id, conid, ticker, sectype,
                                                    quantity, option_type , side , option_expiry_date, 
                                                    option_strike, expired 
                                            FROM public.sim_positions 
                                            WHERE account_id = '{account_id}' 
                                            and sectype = 'STK' ; 
                                        """
                cur.execute(query)
                stk_tups = cur.fetchall()
                if len(stk_tups) > 1:
                    raise Exception("More than one STK positions, possible duplicates")
                else:
                    stk_avail_ind = True if len(stk_tups) == 1 else False

                # get current price for the asset to identify if the contract is In-The-Money for settlement.
                query = f""" select max(last_price) from public.sim_stock_history 
                                where quote_datetime = '{quotetime}'
                                and conid = {spy_con_id};
                                """
                cur.execute(query)
                stk_eod_price_tup = cur.fetchone()
                if len(stk_eod_price_tup) == 0:
                    raise Exception(f"EOD price for SPY not available for {quotetime}")
                stk_eod_price = stk_eod_price_tup[0]
                # Find out if the contract is in the money
                if ((df['option_type'] == 'P' and stk_eod_price <= df['option_strike'])
                        or (df['option_type'] == 'C' and stk_eod_price >= df['option_strike'])):
                    is_in_the_money = True
                else:
                    is_in_the_money = False

                logger.debug(f"Option type : {df['option_type']}, option strike : {df['option_strike']}, "
                             f"stk eod price : {stk_eod_price}, Is it in the money ? : {is_in_the_money}")
                logger.debug(f"type of option_strike : {type(df['option_strike'])}")
                logger.debug(f"type of stk_eod_price : {type(stk_eod_price)}")
                # choose wether to buy or sell the asset to settle
                buy_stk_ind = (df['side'] == 'SELL') & (df['option_type'] == 'P') & (df['sectype'] == 'OPT') \
                              & is_in_the_money
                sell_stk_ind = (df['side'] == 'SELL') & (df['option_type'] == 'C') & stk_avail_ind & is_in_the_money

                logger.debug(f"Is obligation in the money? : {buy_stk_ind}")
                logger.debug(f"buy_stk_ind: {buy_stk_ind}")
                logger.debug(f"sell_stk_ind: {sell_stk_ind}")

                if buy_stk_ind or sell_stk_ind:  # Insert ordr_hist and pos only if there is a settlement scenario.
                    # if there is put that is sold, no calls sold and no stk pos then buy the stock.
                    if buy_stk_ind:
                        settle_qnty = df['quantity'] * -100
                        settle_strike = df['option_strike']
                        settle_ticker = df['ticker']
                        settle_amount = (settle_strike * settle_qnty) * -1
                        side = 'BUY'
                        # calc the new cashbalance
                        next_cash_bal = float(prev_cash_balance) + float(settle_amount)

                        # ***************************************
                        # Insert positions, buy the stock only if the quantity is > 0
                        #   When we collect juice or buy back contract due to the 5% rule
                        #   this api inserts is 0 record STK settlement. thats why we have > 0 check.
                        # ***************************************
                        if settle_qnty > 0:
                            query = f"""
                                    INSERT INTO public.sim_positions (account_id, conid, sectype, quantity, avg_price, 
                                                                      side, ordertype, option_expiry_date, ticker, 
                                                                      option_strike, rec_created_by) 
                                        values ('{account_id}', {spy_con_id}, '{sec_type}', {settle_qnty}, '{settle_strike}',
                                                '{side}', '{settle_order_type}', {not_applicable_num}, '{settle_ticker}', 
                                                 {settle_strike}, '{rec_created_by}')
                                        ON CONFLICT (account_id, conid) 
                                        DO UPDATE 
                                            SET quantity = sim_positions.quantity + EXCLUDED.quantity, 
                                                avg_price = EXCLUDED.avg_price,
                                                rec_created_by = 'Settlement API - Added to existing stks'
                                        ;
                                    """
                            logger.debug("query: {}".format(query))
                            cur.execute(query)
                            # note cur.fetchone() will throw exceptio as "no results to fetch" for inserts.
                            # So using this method
                            pos_insert_count = cur.statusmessage
                            logger.debug("pos_insert_count: " + pos_insert_count)
                        else:
                            logger.debug("No need insert a zero position. "
                                         "Mostly caused by a buy back scenario that left out 0 quantity obligation")
                    elif sell_stk_ind:
                        settle_qnty = df['quantity'] * 100
                        settle_strike = df['option_strike']
                        settle_ticker = df['ticker']
                        settle_amount = (settle_strike * settle_qnty) * -1
                        side = 'SELL'
                        # calc the new cashbalance
                        next_cash_bal = float(prev_cash_balance) + float(settle_amount)
                        # deduct the qty of stocks to be sold from the existins positions
                        # Note: we cannot delete the position record straight away because
                        # GKBOT accumulates stocks over time until a lot is available for
                        # trading.

                        # note: the quantity in DB is negative that why we are deducting the
                        #       settle quantity in the below query.
                        query = f"""
                                update public.sim_positions sp
                                  set quantity = quantity + {settle_qnty}
                                WHERE sp.account_id = '{account_id}'
                                AND conid = {spy_con_id}
                                AND sectype = '{sec_type}'
                                AND ticker = '{settle_ticker}';
                                """
                        logger.debug("query: {}".format(query))
                        cur.execute(query)
                        pos_sell_count = cur.statusmessage
                        logger.debug("pos sold qty: " + pos_sell_count)

                        # Stck will be sold later in the same DB transaction via order api,
                        # so deleting it to mimic the give away of the stock.
                        # and delete positions only if the left over quantity = 0. Which means there were no extras
                        # accumulated that are not part of the traded lots.
                        query = f"""
                                DELETE FROM public.sim_positions sp
                                WHERE account_id = '{account_id}'
                                AND conid = {spy_con_id}
                                AND sectype = '{sec_type}'
                                AND ticker = '{settle_ticker}'
                                AND quantity = 0;
                                """
                        logger.debug("query: {}".format(query))
                        cur.execute(query)
                        # note cur.fetchone() will throw exceptio as "no results to fetch" for inserts.
                        # So using this method
                        pos_delete_count = cur.statusmessage
                        logger.debug("pos_delete_count: " + pos_delete_count)

                    # ****************************************
                    # insert record into order history table.
                    # ****************************************
                    order_id_tup = utils.ins_order_history(account_id=account_id, amount=settle_amount, coid=coid,
                                                           conid=spy_con_id, cur=cur,
                                                           option_expiry_date=not_applicable_num,
                                                           option_strike=not_applicable_num,
                                                           option_type=not_applicable_str,
                                                           ordertype=settle_order_type, parentid=parent_stlmnt_coid,
                                                           price=settle_strike,
                                                           quantity=settle_qnty,
                                                           quote_timestamp=quotetime, rec_created_by=rec_created_by,
                                                           sectype=sec_type, side=side, ticker=settle_ticker)
                    if order_id_tup is None:
                        raise Exception("Unable to insert in to order history and create order id (series col)")
                    order_id = order_id_tup[0][0]
                    logger.debug("order_id: " + str(order_id))

                    # **************************************
                    # insert data into ledger history table
                    # *************************************
                    ledger_id, query = utils.ins_ledger_history(account_id=account_id, amount=settle_amount, cur=cur,
                                                                cur_cash_balance=next_cash_bal, order_id=order_id,
                                                                quote_timestamp=quotetime,
                                                                rec_created_by=rec_created_by)
                self._delete_positions(account_id, cur, query, settle_date)
        except Exception as e:
            logger.error(f"Error executing Query in DB: {query}")
            logger.error(e)
            self.conn.rollback()
            return [{'handled_exception': e.__str__()}]

        return [{"settlement status": f"Positions settled for {settle_date} at {quotetime}"}]

    def _delete_positions(self, account_id, cur, query, settle_date):
        # *******************************************************
        # expire or delete all the open contracts expiring today
        # *******************************************************
        query = f"""
                        delete from public.sim_positions where account_id = '{account_id}' 
                            and option_expiry_date = {settle_date};
                        """
        logger.debug("query: {}".format(query))
        cur.execute(query)
        # note cur.fetchone() will throw exceptio as "no results to fetch" for inserts.
        # So using this method
        del_count = cur.statusmessage
        logger.debug("pos_delete_count: " + del_count)
        return del_count


if __name__ == "__main__":
    logger.setLevel('DEBUG')
    output = None
    # portal_db = PortalDB('local')
    with PortalDB('local') as getPortalDB:
        # getPortalDB.getStrikes(756733, 'DEC15')
        # output = getPortalDB.getinfo(756733, 'JAN11', 'C', '114')
        # getPortalDB.getsnapshot(756733, '31', '2014-08-04 12:15:00')
        # getPortalDB.getsnapshot('2013062810011100', '84,86', '2013-06-28 13:30:00')

        # getPortalDB.putorder(
        #     account_id='DU2387565',
        #     conid=756733,
        #     coid='testLocalOrd:STK1',
        #     parentid='testLocalOrd:STKP11',
        #     ordertype='LIMIT',
        #     price=290,
        #     side='BUY',
        #     ticker='SPY',
        #     sectype='STK',
        #     quantity=600,
        #     quote_timestamp='2013-06-28 13:30:00')

        # getPortalDB.putorder(
        #     account_id='DU2387565',
        #     # conid=2011010710011300,
        #     conid=1998010520011000,
        #     coid='DU2387565:C1',
        #     parentid='DU2387565:P1',
        #     ordertype='LIMIT',
        #     price=2,
        #     side='SELL',
        #     ticker='SPY',
        #     sectype='OPT',
        #     quantity=7,
        #     quote_timestamp='1998-01-02 09:00:00')
        output = getPortalDB.getledger(account_id='gkbot1M-81516', quotetime='2016-10-14 22:15:00')
        # output = getPortalDB.getpositions(account_id='mano1M-1', quotetime='2015-09-11 16:00:00')
        # output = getPortalDB.postsettlement(account_id='stk4-ec2-1s', quotetime='2016-01-22 16:15:00')

        print(output)
