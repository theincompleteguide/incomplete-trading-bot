# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can find at www.theincompleteguide.com
# You will also find improvement ideas and explanations
import databaseMySql
from alpaca_trade_api import rest
from stocklib import *
from traderlib import *
from other_functions import *
import threading, os, logging
from datetime import datetime
import gvars
from assetHandler import AssetHandler
from pytz import timezone

# Global object we log to; the handler will work with any log message
_L = logging.getLogger("demo")


# Create a special logger that logs to per-thread-name files
class MultiHandler(logging.Handler):
    def __init__(self, dirname):
        super(MultiHandler, self).__init__()
        self.files = {}
        self.dirname = dirname
        if not os.access(dirname, os.W_OK):
            raise Exception("Directory %s not writeable" % dirname)

    def flush(self):
        self.acquire()
        try:
            for fp in list(self.files.values()):
                fp.flush()
        finally:
            self.release()

    def _get_or_open(self, key):
        # Get the file pointer for the given key, or else open the file
        self.acquire()
        try:
            if key in self.files:
                return self.files[key]
            else:
                fp = open(os.path.join(self.dirname, "%s.log" % key), "a")
                self.files[key] = fp
                return fp
        finally:
            self.release()

    def emit(self, record):
        # No lock here; following code for StreamHandler and FileHandler
        try:
            fp = self._get_or_open(record.threadName)
            msg = self.format(record)
            fp.write('%s\n' % msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def clean_open_orders(api):
    # First, cancel any existing orders so they don't impact our buying power.
    orders = api.list_orders(status="open")

    print('\nCLEAR ORDERS')
    print('%i orders were found open' % int(len(orders)))

    for order in orders:
        api.cancel_order(order.id)


def check_account_ok(api):
    account = api.get_account()
    if account.account_blocked or account.trading_blocked or account.transfers_blocked:
        print('OJO, account blocked. WTF?')
        import pdb;
        pdb.set_trace()


def run_tbot(_L, assHand, account):
    # initialize trader object
    trader = Trader(gvars.API_KEY, gvars.API_SECRET_KEY, _L, account)

    while True:

        ticker = assHand.find_target_asset()
        stock = Stock(ticker)

        ticker, lock = trader.run(stock)  # run the trading program

        if lock:  # if the trend is not favorable, lock it temporarily
            assHand.lock_asset(ticker)
        else:
            assHand.make_asset_available(ticker)


def set_alpaca_api():
    auth = databaseMySql.get_key_secrets('PAPER')
    live = databaseMySql.get_key_secrets('LIVE')
    gvars.ALPACA_API_URL = live[0]
    gvars.API_KEY = live[1]
    gvars.API_SECRET_KEY = live[2]
    os.environ['APCA_API_KEY_ID'] = gvars.API_KEY
    os.environ['APCA_API_SECRET_KEY'] = gvars.API_SECRET_KEY


def main():
    # Set up a basic stderr logging; this is nothing fancy.
    log_format = '%(asctime)s %(threadName)12s: %(lineno)-4d %(message)s'
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(stderr_handler)

    # Set up a logger that creates one file per thread
    todayLogsPath = create_log_folder(gvars.LOGS_PATH)
    multi_handler = MultiHandler(todayLogsPath)
    multi_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(multi_handler)

    # Set default log level, log a message
    _L.setLevel(logging.DEBUG)
    _L.info("\n\n\nRun initiated")
    _L.info('Max workers allowed: ' + str(gvars.MAX_WORKERS))

    # initialize the API with Alpaca
    api = tradeapi.REST(gvars.API_KEY, gvars.API_SECRET_KEY, gvars.ALPACA_API_URL, api_version='v2')

    # initialize the asset handler
    assHand = AssetHandler()

    # get the Alpaca account ready
    try:
        _L.info("Getting account")
        check_account_ok(api)  # check if it is ok to trade
        account = api.get_account()
        clean_open_orders(api)  # clean all the open orders
        _L.info("Got it")
    except Exception as e:
        _L.info(str(e))

    for thread in range(gvars.MAX_WORKERS):  # this will launch the threads
        worker = 'th' + str(thread)  # establishing each worker name

        worker = threading.Thread(name=worker, target=run_tbot, args=(_L, assHand, account))
        worker.start()  # it runs a run_tbot function, declared here as well

        time.sleep(1)


def is_market_open():
    api = tradeapi.REST(gvars.API_KEY, gvars.API_SECRET_KEY, gvars.ALPACA_API_URL, api_version='v2')
    is_open = api.get_clock().is_open
    while not is_open:
        clock = api.get_clock()
        opening_time = clock.next_open.replace().timestamp()
        curr_time = clock.timestamp.replace().timestamp()
        time_to_open = int((opening_time - curr_time) / 60)

        print(str(time_to_open) + " minutes til market open. " + display_time(time_to_open/0.016667))

        time.sleep(60)
        is_open = api.get_clock().is_open

    return is_open


intervals = (
    ('days', 86400),  # 60 * 60 * 24
    ('hours', 3600),  # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


if __name__ == '__main__':
    set_alpaca_api()

    if is_market_open():
        main()
