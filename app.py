from chalice import Chalice
from chalicelib.lambda_handlers import secdef_strikes_api, \
    secdef_info_api, market_snapshot_api, account_order_api, \
    portfolio_ledger_api, portfolio_positions_api, settlement_api
import logging

app = Chalice(app_name='gkportal')
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


def _get_event(_app: Chalice):
    request = _app.current_request
    event = request.query_params
    context = request.context
    body = request.json_body
    return event, context, body


@app.route('/v1/api/iserver/secdef/strikes', methods=['GET'])
def secdefstrikes():
    event, context, body = _get_event(app)
    return secdef_strikes_api(event, context)
    # :TODO return app.current_request.to_dict() [ TO do debug the params in cloud log stream ]


@app.route('/v1/api/iserver/secdef/info', methods=['GET'])
def secdefinfo():
    event, context, body = _get_event(app)
    return secdef_info_api(event, context)


@app.route('/v1/api/iserver/marketdata/snapshot', methods=['GET'], content_types=['application/json'])
def marketdatasnapshot():
    event, context, body = _get_event(app)
    return market_snapshot_api(event, context)


@app.route('/v1/api/iserver/account/{account_id}/order', methods=['POST'])
def accountorder(account_id):
    event, context, body = _get_event(app)
    # assign ther paylopad from the API req as event for the lambda
    event.update(body)
    event['account_id'] = account_id
    return account_order_api(event, context)


@app.route('/v1/api/portfolio/{account_id}/ledger', methods=['GET'])
def portfolioledger(account_id):
    event, context, body = _get_event(app)
    event['account_id'] = account_id
    return portfolio_ledger_api(event, context)


@app.route('/v1/api/portfolio/{account_id}/positions/{page_id}', methods=['GET'])
def positions(account_id, page_id):
    event, context, body = _get_event(app)
    event['account_id'] = account_id
    return portfolio_positions_api(event, context)


@app.route('/v1/api/iserver/accounts', methods=['GET'])
def accounts():
    return {"accounts": "Dummy response from compatibility"}


@app.route('/v1/api/portfolio/subaccounts', methods=['GET'])
def subaccounts():
    return {"subaccounts": "Dummy response from compatibility"}


@app.route('/v1/api/iserver/secdef/search', methods=['POST'])
def search():
    return { "conid": 756733, "symbol": "SPY", "description": "Defaulted Conid in SIMPAI" }


@app.route('/gkportal/{account_id}/settle', methods=['POST'])
def settlement(account_id):
    event, context, body = _get_event(app)
    event['account_id'] = account_id
    return settlement_api(event, context)


@app.route('/v1/api/iserver/reply/{reply_id}', methods=['POST'])
def reply_order(reply_id):
    return {"GK Portal Status": "Reply acknowledged"}


@app.route('/v1/api/sso/validate', methods=['GET'])
def validate():
    return {"GK Portal Status": "Validation Simulated"}


@app.route('/v1/api/portfolio/{account_id}/positions/invalidate', methods=['GET'])
def invalidate(account_id):
    return {"GK Portal Status": "Positions Invalidate Simulated"}


@app.route('/v1/api/iserver/account/{account_id}/order/{order_id}', methods=['DELETE'])
def delete_order(account_id, order_id):
    return {"GK Portal Status" : "Order Delete Simulated"}


@app.route('/v1/api/iserver/account/orders', methods=['GET'])
def orders_status():
    return {"orders": [{"status": "filled"}]}
