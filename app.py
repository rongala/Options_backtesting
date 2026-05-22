from chalice import Chalice, Response
from typing import Dict, Any, Optional
from chalicelib.lambda_handlers import (
    secdef_strikes_api, secdef_info_api, market_snapshot_api,
    account_order_api, portfolio_ledger_api, portfolio_positions_api,
    settlement_api
)
from chalicelib.setup_logger import get_logger

app = Chalice(app_name='gkportal')
logger = get_logger(__name__, level='DEBUG')


def _extract_event(request_query_params: Optional[Dict[str, str]],
                   request_context: Dict[str, Any],
                   request_json_body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract event from request data.
    
    @param request_query_params: Query parameters from request
    @param request_context: Request context
    @param request_json_body: JSON body from request
    @return: Combined event dictionary
    """
    event = request_query_params or {}
    if request_json_body:
        event.update(request_json_body)
    return event


@app.route('/v1/api/iserver/secdef/strikes', methods=['GET'])
def secdefstrikes() -> Dict[str, Any]:
    """Get available strike prices for options."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    return secdef_strikes_api(event, request.context)


@app.route('/v1/api/iserver/secdef/info', methods=['GET'])
def secdefinfo() -> Any:
    """Get option contract information."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    return secdef_info_api(event, request.context)


@app.route('/v1/api/iserver/marketdata/snapshot', methods=['GET'], content_types=['application/json'])
def marketdatasnapshot() -> Any:
    """Get market snapshot (prices, bid/ask)."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    return market_snapshot_api(event, request.context)


@app.route('/v1/api/iserver/account/{account_id}/order', methods=['POST'])
def accountorder(account_id: str) -> Dict[str, Any]:
    """Place an order."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    event['account_id'] = account_id
    return account_order_api(event, request.context)


@app.route('/v1/api/portfolio/{account_id}/ledger', methods=['GET'])
def portfolioledger(account_id: str) -> Dict[str, Any]:
    """Get portfolio ledger (cash balance, net liquidation value)."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    event['account_id'] = account_id
    return portfolio_ledger_api(event, request.context)


@app.route('/v1/api/portfolio/{account_id}/positions/{page_id}', methods=['GET'])
def positions(account_id: str, page_id: str) -> Any:
    """Get open positions."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    event['account_id'] = account_id
    return portfolio_positions_api(event, request.context)


@app.route('/v1/api/iserver/accounts', methods=['GET'])
def accounts() -> Dict[str, str]:
    """Dummy response for compatibility."""
    return {"accounts": "Dummy response from compatibility"}


@app.route('/v1/api/portfolio/subaccounts', methods=['GET'])
def subaccounts() -> Dict[str, str]:
    """Dummy response for compatibility."""
    return {"subaccounts": "Dummy response from compatibility"}


@app.route('/v1/api/iserver/secdef/search', methods=['POST'])
def search() -> Dict[str, Any]:
    """Search for securities."""
    return {"conid": 756733, "symbol": "SPY", "description": "Defaulted Conid in SIMPAI"}


@app.route('/gkportal/{account_id}/settle', methods=['POST'])
def settlement_endpoint(account_id: str) -> Dict[str, Any]:
    """Settle positions."""
    request = app.current_request
    event = _extract_event(request.query_params, request.context, request.json_body)
    event['account_id'] = account_id
    return settlement_api(event, request.context)


@app.route('/v1/api/iserver/reply/{reply_id}', methods=['POST'])
def reply_order(reply_id: str) -> Dict[str, str]:
    """Acknowledge reply to order."""
    return {"GK Portal Status": "Reply acknowledged"}


@app.route('/v1/api/sso/validate', methods=['GET'])
def validate() -> Dict[str, str]:
    """Validate SSO."""
    return {"GK Portal Status": "Validation Simulated"}


@app.route('/v1/api/portfolio/{account_id}/positions/invalidate', methods=['GET'])
def invalidate(account_id: str) -> Dict[str, str]:
    """Invalidate positions."""
    return {"GK Portal Status": "Positions Invalidate Simulated"}


@app.route('/v1/api/iserver/account/{account_id}/order/{order_id}', methods=['DELETE'])
def delete_order(account_id: str, order_id: str) -> Dict[str, str]:
    """Delete an order."""
    return {"GK Portal Status": "Order Delete Simulated"}


@app.route('/v1/api/iserver/account/orders', methods=['GET'])
def orders_status() -> Dict[str, Any]:
    """Get order status."""
    return {"orders": [{"status": "filled"}]}
