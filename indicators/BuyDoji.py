import os

import alpaca_trade_api as tradeapi
import databaseMySql
import gvars
from alpaca_trade_api import StreamConn
import threading
import time
import datetime
import logging
import argparse
import schedule
import time

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# API KEYS
#region
API_LIVE_KEY      = ""
API_LIVE_SECRET   = ""
API_KEY           = ""
API_SECRET        = ""
APCA_API_BASE_URL = ""

#endregion

def job(alpaca_live):
    print("I'm working...")
    ass = alpaca_live.get_asset("MSFT")
    bar = alpaca_live.get_barset("MSFT", '5Min', 1)

    print(bar)
    symbol = bar['MSFT'].symbol
    print("Close: ", bar.close)
    print("Open: ", bar.open)
    print("Low: ", bar.low)
    print(symbol)
    # Check for Doji
    if bar.close > bar.open and bar.open - bar.low > 0.1:
        print('Buying on Doji!')

#Buy a stock when a doji candle forms
class BuyDoji:
  def __init__(self):
    auth     = databaseMySql.get_key_secrets('PAPER')
    live     = databaseMySql.get_key_secrets('LIVE')

    APCA_API_BASE_URL = live[0]
    API_KEY           = live[1]
    API_SECRET        = live[2]
    API_LIVE_KEY      = live[1]
    API_LIVE_SECRET   = live[2]

    gvars.ALPACA_API_URL = live[0]
    gvars.API_KEY        = live[1]
    gvars.API_SECRET_KEY = live[2]

    os.environ['APCA_API_KEY_ID'] = gvars.API_KEY
    os.environ['APCA_API_SECRET_KEY'] = gvars.API_SECRET_KEY

    self.alpaca = tradeapi.REST(API_KEY, API_SECRET, APCA_API_BASE_URL, api_version='v2')

    schedule.every(20).seconds.do(job(self.alpaca))
    while True:
        schedule.run_pending()
        time.sleep(1)

  def run(self):
        #On Each Minute
        async def on_minute(conn, channel, bar):
            symbol = bar.symbol
            print("Close: ", bar.close)
            print("Open: ", bar.open)
            print("Low: ", bar.low)
            print(symbol)
            #Check for Doji
            if bar.close > bar.open and bar.open - bar.low > 0.1:
                print('Buying on Doji!')
                # self.alpaca.submit_order(symbol,1,'buy','market','day')
            #TODO : Take profit

        #Connect to get streaming market data
        conn = StreamConn(API_LIVE_KEY, API_LIVE_SECRET, 'wss://alpaca.socket.polygon.io/stocks')
        on_minute = conn.on(r'AM$')(on_minute)
        # Subscribe to Microsoft Stock
        conn.run(['AM.MSFT'])

# Run the BuyDoji class
ls = BuyDoji()
ls.run()
