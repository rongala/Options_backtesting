import json
from chalicelib.setup_logger import get_logger
from chalicelib.service import PortalService
from chalicelib.repository import PortalDB

logger = get_logger(__name__)


def secdef_strikes_api(event: dict, context: dict) -> dict:
    """
    lambda backend for iserver/secdef/strikes/ endpoint.

    Sample parameters from rest url:
    /iserver/secdef/strikes?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&stage=dev

    Sample response:
        {"call": ["252.50", "150.00"], "put": ["198.00", "140.50"]}

    """
    with PortalDB(event["stage"]) as strksdb:
        strkssrvc: PortalService = PortalService(strksdb)
        output = strkssrvc.getStrikeSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def secdef_info_api(event: dict, context: dict) -> list:
    """
       lambda backend for iserver/secdef/info/ endpoint.

       Sample parameters from rest url:
       /iserver/secdef/info?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&strike=189&right=C&stage=dev

       Sample response:
           [
                {"conid": "2013010410012400","strike": "124","right": "C","maturityDate": 20130104},
                {"conid": "2013011110012400","strike": "124","right": "C","maturityDate": 20130111}
            ]

       """
    with PortalDB(event["stage"]) as infodb:
        infosrvc: PortalService = PortalService(infodb)
        output = infosrvc.getInfoSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def market_snapshot_api(event: dict, context: dict) -> list:
    """
       lambda backend for iserver/secdef/snapshot/ endpoint.

       Sample parameters from rest url:
       /iserver/secdef/info?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&strike=189&right=C&stage=dev

       Sample response:
           [
                {"conid": "2013010410012400","strike": "124","right": "C","maturityDate": 20130104},
                {"conid": "2013011110012400","strike": "124","right": "C","maturityDate": 20130111}
            ]

       """
    with PortalDB(event["stage"]) as infodb:
        snpshtsrvc: PortalService = PortalService(infodb)
        output = snpshtsrvc.getSnapshotSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def account_order_api(event: dict, context: dict) -> dict:
    """
       lambda backend for iserver/secdef/snapshot/ endpoint.

       Sample parameters from rest url:
       /iserver/secdef/info?acctId=DU2554692&conid=435098432&secType=OPT&cOID=DU2554692-1234
                        &parentId=DU2554692-1234&orderType=LIMIT&listingExchange=SMART
                        &price=0.41&side=SELL&ticker=SPY&tif=AY
                        &referrer=QuickTrade&quantity=29&useAdaptive=true&stage=dev

       Sample response:
           [
                {"conid": "2013010410012400","strike": "124","right": "C","maturityDate": 20130104},
                {"conid": "2013011110012400","strike": "124","right": "C","maturityDate": 20130111}
            ]

       """
    with PortalDB(event["stage"]) as infodb:
        ordrsrvc: PortalService = PortalService(infodb)
        output = ordrsrvc.putOrderSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def portfolio_ledger_api(event: dict, context: dict) -> dict:
    """

    Sample parameters from rest url:
        portfolio/DU2387565/ledger?stage=dev

    sample response:
        {"account_id": "DU2387565", "cashbalace": "8570.00"}
    """
    with PortalDB(event["stage"]) as infodb:
        ldgrsrvc: PortalService = PortalService(infodb)
        output = ldgrsrvc.getLedgerSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def portfolio_positions_api(event: dict, context: dict) -> list:
    """
    lambda backend for portal/portfolio/DU2387565/positions/0

    Sample parameters from rest url:
       /portal/portfolio/DU2387565/positions/0?stage=local

   Sample response:
       [{"acctId": "DU2387565", "conid": "435098432", "ticker": "SPY", "assetClass": "STK", "position": "700",
                "putOrCall": "N/A", "right": "BUY", "expiry": "-999", "strike": "-999.00", "expired": false,
                "rec_created_datetime": "2020-09-21 23:37:07.07675",
                "rec_updated_datetime": "2020-09-21 23:37:07.07675", "rec_created_by": "ORDER API"},
        {"acctId": "DU2387565", "conid": "2015120410019100", "ticker": "SPY", "assetClass": "OPT",
                "position": "-7", "putOrCall": "C", "right": "SELL", "expiry": "20151204", "strike": "191.00",
                "expired": false, "rec_created_datetime": "2020-09-21 23:37:11.19061",
                "rec_updated_datetime": "2020-09-21 23:37:11.19061", "rec_created_by": "ORDER API"},
        {"acctId": "DU2387565", "conid": "2015120420019250", "ticker": "SPY", "assetClass": "OPT",
                "position": "7", "putOrCall": "P", "right": "BUY", "expiry": "20151204", "strike": "112.00",
                "expired": false, "rec_created_datetime": "2020-09-21 23:37:14.56719",
                "rec_updated_datetime": "2020-09-21 23:37:44.19531", "rec_created_by": "ORDER API"}
        ]



    """
    with PortalDB(event["stage"]) as infodb:
        possrvc: PortalService = PortalService(infodb)
        output = possrvc.getPositionsSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def settlement_api(event: dict, context: dict) -> dict:
    """

    Sample parameters from rest url:
        gkportal/DU2387565/settle?quotetime=2013-06-28%2013:30:00&stage=dev

    sample response:
        {'GK Portal Status': 'Settlement done for : 2013-06-28 13:30:00'}
    """
    with PortalDB(event["stage"]) as infodb:
        ldgrsrvc: PortalService = PortalService(infodb)
        output = ldgrsrvc.postSettlementSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


def settlement_api(event: dict, context: dict) -> dict:
    """

    Sample parameters from rest url:
        gkportal/DU2387565/settle?quotetime=2013-06-28%2013:30:00&stage=dev

    sample response:
        {'GK Portal Status': 'Settlement done for : 2013-06-28 13:30:00'}
    """
    with PortalDB(event["stage"]) as infodb:
        ldgrsrvc: PortalService = PortalService(infodb)
        output = ldgrsrvc.postSettlementSrvc(event)
        logger.info("lambda output : " + json.dumps(output))
    return output


if __name__ == "__main__":
    logger.setLevel('DEBUG')
    eventl = {"conid": 756733, "month": "DEC15", "sectype": "OPT", "exchange": "SMART", "stage": "local"}
    contextl = {"context": "sample lambda context"}
    snpsht_31_event_in = {"conid": '756733', "fields": '31', "quotetime": '2014-08-04 12:15:00',
                          "stage": "local"}
    snpsht_84_86_evt_in = {"conid": '2013062810011100', "fields": '84,86', "quotetime": '2013-06-28 13:30:00',
                           "stage": "local"}
    buy_stk_ordr_evt_in = {"account_id": "DU2387565", "conid": 756733, "price": 100,"quantity": 10, "secType": "STK",
                           "cOID": "testLocalOrd:C1",
                           "parentId": "testLocalOrd:P1", "orderType": "LIMIT", "listingExchange": "SMART",
                           "side": "BUY", "ticker": "SPY", "tif": "DAY", "referrer": "QuickTrade",
                           "useAdaptive": True, "stage": "local", "quotetime": '2013-06-28 13:30:00'
                           }
    settlement_event = {"account_id": "DU2387565", "quotetime": '1998-01-02 09:00:00', "stage": "local"}
    # Executre lambda handler

    # secdef_strikes_api(eventl, contextl)
    # secdef_info_api(eventl, contextl)
    # market_snapshot_api(snpsht_31_event_in, contextl)
    # secdef_snapshot_api(snpsht_84_86_evt_in, contextl)
    account_order_api(buy_stk_ordr_evt_in, contextl)
    # portfolio_ledger_api(buy_stk_ordr_evt_in, contextl)
    # portfolio_positions_api(buy_stk_ordr_evt_in, contextl)
    # settlement_api(settlement_event, contextl)
