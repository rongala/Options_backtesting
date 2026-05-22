import json
from chalicelib.setup_logger import get_logger
from chalicelib.utils import missing_parameters
from chalicelib.repository import PortalDB
from decimal import Decimal

logger = get_logger(__name__)


class PortalService:
    def __init__(self, portal_db: PortalDB):
        self.portal_db = portal_db

    def get_strike_srvc(self, event: dict) -> dict:
        """
        Returns a dict of strikes for call and put options from back testing data.
        expected to simulate iserver/secdef/strikes end point from IBKR client portal API.

        sample output:
            {"call": ["252.50", "150.00"], "put": ["198.00", "140.50"]}
        """
        req_keys = ['conid', 'month']
        call_strike_list = []
        put_strike_list = []
        # validate parameters
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return {
                "error": "Missing Parameters: " + ", ".join(missing_params)
            }

        records = self.portal_db.get_strikes(conid=int(event['conid']), month=event['month'])
        for row in records:
            if row[0] == 'C':
                call_strike_list.append(row[1])
            elif row[0] == 'P':
                put_strike_list.append(row[1])
            else:
                custom_error = '\n Found invalid option_type : ' + row[0]
                raise Exception(custom_error)
        output = {"call": call_strike_list, "put": put_strike_list}
        logger.debug("get_strike_srvc output: " + json.dumps(output))
        return output

    def get_info_srvc(self, event: dict) -> list:
        """
        returns all the option contracts for
            the underlying asset's (SPY) conid, month, strike and option_type a.k.a right.

        Sample Output:
        --------------
        [{'conid': 2015120410018900, 'strike': '189', 'right': 'C', 'maturityDate': 20151204},
        {'conid': 2015120410018900, 'strike': '189', 'right': 'C', 'maturityDate': 20151211},
        {'conid': 2015120410018900, 'strike': '189', 'right': 'C', 'maturityDate': 20151218},
        {'conid': 2015120410018900, 'strike': '189', 'right': 'C', 'maturityDate': 20151219},
        {'conid': 2015120410018900, 'strike': '189', 'right': 'C', 'maturityDate': 20151224},
        {'conid': 2015120410018900, 'strike': '189', 'right': 'C', 'maturityDate': 20151231}
        ]

        """
        req_keys = ['conid', 'month', 'strike', 'right']
        output_cols = ['conid', 'strike', 'right', 'maturityDate']
        output = []
        # validate parameters
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return [{"Missing parameters Error": missing_params}]
        records = self.portal_db.get_info(conid=int(event['conid']), month=event['month'],
                                        option_type=event['right'], strike=event['strike'])
        for rec in records:
            output.append(dict(zip(output_cols, rec)))
        logger.debug(output)
        return output

    def get_snapshot_srvc(self, event: dict) -> list:
        """
        returns the current price (31), bid price(84) and ask price(86) for the requested conid and quote_datetime.

        Sample Output:
        -------------
        [{'conid': 2013062810011100, '31': '329.56'}]
        [{'conid': 2013062810011100, '84': '47.8500', '86': '52.0000'}]

        """
        req_keys = ['conids', 'quotetime']
        if event['fields'] == '31':
            output_cols = ['conid', '31']
        elif event['fields'] == '84,86':
            output_cols = ['conid', '84', '86']
        else:
            raise Exception("only fields allowed : 31, 84, 86")

        output = []
        # validate parameters
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return [{"Missing parameters Error": missing_params}]
        records = self.portal_db.get_snapshot(conids=event['conids'], fields=event['fields'],
                                               quotetime=event['quotetime'])
        # logger.debug(records)
        for rec in records:
            output.append(dict(zip(output_cols, rec)))
        logger.debug(output)
        return output

    def put_order_srvc(self, event: dict) -> list:
        """
        places order to order history, updates ledger history and positions data.

        """
        # note there are 2 acct ids coming in the request. 1) account_id from path param and 2) acctID from query param.
        # since path param is mandatory, we are using the first one.
        req_keys = ['account_id', 'conid', 'cOID', 'parentId', 'orderType', 'price', 'side', 'ticker', 'quantity']
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return [{"Missing parameters Error": missing_params}]
        output = self.portal_db.put_order(account_id=event['account_id'], conid=event['conid'],
                                           coid=event['cOID'], parentid=event['parentId'],
                                           ordertype=event['orderType'], price=Decimal(event['price']),
                                           side=event['side'], ticker=event['ticker'], sectype=event['secType'],
                                           quantity=Decimal(event['quantity']), quote_timestamp=event['quotetime'])
        logger.debug(output)
        return output

    def get_ledger_srvc(self, event: dict) -> dict:
        """
        returns cashbalance for the requested account.

        @param event:
        @return:

        Sample Output:
        -------------
        {'account_id': 'DU2387565', 'cashbalace': '8570.00'}

        """
        req_keys = ['account_id', 'quotetime']
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return {"Missing parameters Error": missing_params}
        output_list = self.portal_db.get_ledger(account_id=event['account_id'], quotetime=event['quotetime'])
        cashbalance = 0
        netliquidationvalue = 0

        if output_list is None:
            output = {"account_id": event['account_id'], "USD": {"cashbalance": cashbalance, "netliquidationvalue": netliquidationvalue}}
        else:
            # TODO: Figure out a way to serialize decimal instead of converting to float.
            #       Float convertion is a temp solution.
            for val_tuple in output_list:
                if val_tuple[1] == 'cashbalance':
                    cashbalance = float(val_tuple[0]) if val_tuple[0] is not None else 0
                elif val_tuple[1] == 'netliquidationvalue':
                    netliquidationvalue = float(val_tuple[0]) if val_tuple[0] is not None else 0
            output = {"account_id": event['account_id'], "USD": {"cashbalance": cashbalance, "netliquidationvalue": netliquidationvalue + cashbalance}}
        logger.debug(output)
        return output

    def get_positions_srvc(self, event: dict) -> list:
        """
        returns all the current positions held by the account.

        @param event:
        @return:

        Sample Output:
        --------------
        [
        {'acctId': 'DU2387565', 'conid': '435098432', 'ticker': 'SPY', 'assetClass': 'STK', 'position': '700',
                'putOrCall': 'N/A', 'right': 'BUY', 'expiry': '-999', 'strike': '-999.00', 'expired': False,
                'rec_created_datetime': '2020-09-21 23:37:07.07675',
                'rec_updated_datetime': '2020-09-21 23:37:07.07675', 'rec_created_by': 'ORDER API'},
        {'acctId': 'DU2387565', 'conid': '2015120410019100', 'ticker': 'SPY', 'assetClass': 'OPT', 'position': '-7',
                'putOrCall': 'C', 'right': 'SELL', 'expiry': '20151204', 'strike': '191.00', 'expired': False,
                'rec_created_datetime': '2020-09-21 23:37:11.19061',
                'rec_updated_datetime': '2020-09-21 23:37:11.19061', 'rec_created_by': 'ORDER API'},
        {'acctId': 'DU2387565', 'conid': '2015120420019250', 'ticker': 'SPY', 'assetClass': 'OPT', 'position': '7',
                'putOrCall': 'P', 'right': 'BUY', 'expiry': '20151204', 'strike': '112.00', 'expired': False,
                'rec_created_datetime': '2020-09-21 23:37:14.56719',
                'rec_updated_datetime': '2020-09-21 23:37:44.19531', 'rec_created_by': 'ORDER API'}
        ]

        """
        output = []
        req_keys = ['account_id']
        output_cols = ['acctId', 'conid', 'ticker', 'assetClass', 'position', 'putOrCall', 'right',
                       'expiry', 'strike', 'expired', 'rec_created_datetime', 'rec_updated_datetime', 'rec_created_by',
                       'mktPrice', 'avgPrice']
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return [{"Missing parameters Error": missing_params}]
        records = self.portal_db.get_positions(account_id=event['account_id'], quotetime=event['quotetime'])
        for rec in records:
            output.append(dict(zip(output_cols, rec)))
        logger.debug(output)
        return output

    def post_settlement_srvc(self, event: dict) -> list:
        """
        Settles the open positions at the end of the day.

        """
        # note there are 2 acct ids coming in the request. 1) account_id from path param and 2) acctID from query param.
        # since path param is mandatory, we are using the first one.
        req_keys = ['account_id', 'quotetime']
        missing_params = missing_parameters(req_keys, event)
        if missing_params:
            return [{"Missing parameters Error": missing_params}]
        output = self.portal_db.post_settlement(account_id=event['account_id'], quotetime=event['quotetime'])
        logger.debug(output)
        return output


if __name__ == "__main__":
    logger.setLevel('DEBUG')
    event_in = {"conid": 756733, "month": "JAN98", "sectype": "OPT", "exchange": "SMART", "strike": 110,
                "right": "SELL", "stage": "local"}
    event_info_in = {"conid": 756733, "month": "JAN98", "sectype": "OPT", "exchange": "SMART", "strike": 110,
                     "right": "C", "stage": "local"}
    snpsht_31_event_in = {"conid": '756733', "fields": '31', "quotetime": '1998-01-02 09:00:00',
                          "stage": "local"}
    snpsht_84_86_evt_in = {"conid": '1998010520011000', "fields": '84,86', "quotetime": '1998-01-02 09:00:00',
                           "stage": "local"}
    ordr_buy_spy_evt_in = {"account_id": "DU2387565", "conid": 756733, "price": 10, "quantity": 1, "secType": "STK",
                           "cOID": "testLocalOrd:C1",
                           "parentId": "testLocalOrd:P1", "orderType": "LIMIT", "listingExchange": "SMART",
                           "side": "BUY", "ticker": "SPY", "tif": "DAY", "referrer": "QuickTrade",
                           "useAdaptive": True, "stage": "local", "quotetime": '1998-01-02 09:00:00'
                           }
    settlement_event = {"account_id": "gkbot1M-81516", "quotetime": '2016-10-14 10:15:00'}

    # Instantiate and dependency Injection
    with PortalDB(event_in["stage"]) as getPortalDB:
        getSrvc = PortalService(getPortalDB)
        # getSrvc.get_strike_srvc(event_in)
        # getSrvc.get_info_srvc(event_info_in)
        # getSrvc.get_snapshot_srvc(snpsht_31_event_in)
        # getSrvc.get_snapshot_srvc(snpsht_84_86_evt_in)
        # getSrvc.put_order_srvc(ordr_buy_spy_evt_in)
        getSrvc.get_ledger_srvc(settlement_event)
        # getSrvc.get_positions_srvc(ordr_buy_spy_evt_in)
        # getSrvc.post_settlement_srvc(settlement_event)
