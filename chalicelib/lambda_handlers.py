import json
from typing import Dict, List, Any
from chalicelib.setup_logger import get_logger
from chalicelib.service import PortalService
from chalicelib.repository import PortalDB

logger = get_logger(__name__)


def secdef_strikes_api(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Lambda handler for iserver/secdef/strikes endpoint."""
    try:
        with PortalDB(event["stage"]) as strksdb:
            strkssrvc = PortalService(strksdb)
            output = strkssrvc.get_strike_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in secdef_strikes_api: {e}")
        return {"error": str(e)}


def secdef_info_api(event: Dict[str, Any], context: Dict[str, Any]) -> List:
    """Lambda handler for iserver/secdef/info endpoint."""
    try:
        with PortalDB(event["stage"]) as infodb:
            infosrvc = PortalService(infodb)
            output = infosrvc.get_info_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in secdef_info_api: {e}")
        return [{"error": str(e)}]


def market_snapshot_api(event: Dict[str, Any], context: Dict[str, Any]) -> List:
    """Lambda handler for iserver/marketdata/snapshot endpoint."""
    try:
        with PortalDB(event["stage"]) as infodb:
            snpshtsrvc = PortalService(infodb)
            output = snpshtsrvc.get_snapshot_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in market_snapshot_api: {e}")
        return [{"error": str(e)}]


def account_order_api(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Lambda handler for iserver/account/{account_id}/order endpoint."""
    try:
        with PortalDB(event["stage"]) as infodb:
            ordrsrvc = PortalService(infodb)
            output = ordrsrvc.put_order_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in account_order_api: {e}")
        return {"error": str(e)}


def portfolio_ledger_api(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Lambda handler for portfolio/{account_id}/ledger endpoint."""
    try:
        with PortalDB(event["stage"]) as infodb:
            ldgrsrvc = PortalService(infodb)
            output = ldgrsrvc.get_ledger_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in portfolio_ledger_api: {e}")
        return {"error": str(e)}


def portfolio_positions_api(event: Dict[str, Any], context: Dict[str, Any]) -> List:
    """Lambda handler for portfolio/{account_id}/positions endpoint."""
    try:
        with PortalDB(event["stage"]) as infodb:
            possrvc = PortalService(infodb)
            output = possrvc.get_positions_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in portfolio_positions_api: {e}")
        return [{"error": str(e)}]


def settlement_api(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Lambda handler for settlement endpoint."""
    try:
        with PortalDB(event["stage"]) as infodb:
            ldgrsrvc = PortalService(infodb)
            output = ldgrsrvc.post_settlement_srvc(event)
            logger.info(f"lambda output : {json.dumps(output)}")
        return output
    except Exception as e:
        logger.error(f"Error in settlement_api: {e}")
        return {"error": str(e)}
