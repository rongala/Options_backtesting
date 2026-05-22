# About SIMAPI
SIMAPI is a simulation of IBKR rest endpoints to provide testing framework with time travel capabilities and makes up 
a lack of non-realtime based test platform from IBKR.

# Resources to understand chalice apps
https://aws.github.io/chalice/quickstart.html
https://medium.com/swlh/getting-started-with-chalice-to-create-aws-lambdas-in-python-step-by-step-tutorial-3ccf01701259

# initial setup to work in venv
cd my-project
virtualenv venv
.\venv\bin\activate
pip freeze > requirements.txt
deactivate

# run app locally
chalice local

### To test deploy to stage test before deploying
chalice deploy --profile devwest --stage test

# deploy Chalice app to west - using raj local profiles
chalice deploy --profile devwest

# Sample chalice local endpoints
localhost:8000/iserver/secdef/strikes?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&stage=local
localhost:8000/iserver/secdef/info?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&strike=189&right=C&stage=local
localhost:8000/marketdata/snapshot?conid=756733&fields=31&quotetime=2014-08-04%2012:15:00&stage=local
localhost:8000/marketdata/snapshot?conid=2013062810011100&fields=84,86&quotetime=2013-06-28%2013:30:00&stage=local
localhost:8000/account/order?acctID=DU2387565&conid=435098432&secType=STK&cOID=DU2387565:C1&parentId=DU2387565:P1&orderType=LIMIT&listingExchange=SMART&price=290&side=BUY&ticker=SPY&tif=AY&referrer=QuickTrade&quantity=6&useAdaptive=true&quotetime=2013-06-28%2013:30:00&stage=local

# Sample chalice dev endpoints
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/iserver/secdef/strikes?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev//iserver/secdef/info?conid=756733&month=DEC15&sectype=OPT&exchange=SMART&strike=189&right=C&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/marketdata/snapshot?conid=756733&fields=31&quotetime=2014-08-04%2012:15:00&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/marketdata/snapshot?conid=2013062810011100&fields=84,86&quotetime=2013-06-28%2013:30:00&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/account/order?acctID=DU2387565&conid=435098432&secType=STK&cOID=DU2387565:C1&parentId=DU2387565:P1&orderType=LIMIT&listingExchange=SMART&price=290&side=BUY&ticker=SPY&tif=AY&referrer=QuickTrade&quantity=6&useAdaptive=true&quotetime=2013-06-28%2013:30:00&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/account/order?acctID=DU2387565&conid=2013062810011100&secType=OPT&cOID=DU2387565:C1&parentId=DU2387565:P1&orderType=LIMIT&listingExchange=SMART&price=4.7&side=SELL&ticker=SPY&tif=AY&referrer=QuickTrade&quantity=6&useAdaptive=true&quotetime=2013-06-28%2013:30:00&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/account/order?acctID=DU2387565&conid=2013062810231100&secType=OPT&cOID=DU2387565:C1&parentId=DU2387565:P1&orderType=LIMIT&listingExchange=SMART&price=1.3&side=BUY&ticker=SPY&tif=AY&referrer=QuickTrade&quantity=6&useAdaptive=true&quotetime=2013-06-28%2013:30:00&stage=dev
https://44h5wh7wt0.execute-api.us-west-2.amazonaws.com/dev/portfolio/DU2387565/ledger?stage=dev


