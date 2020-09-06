import tbot
from bots import buy_bot, sell_bot
from database import databaseMySql
from stocklib import *
from traderlib import *
from other_functions import *
import threading, os, logging
from assetHandler import AssetHandler


# Global object we log to; the handler will work with any log message
_L = logging.getLogger("demo")
alpaca_api = None


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
        except Exception as e:
            self.handleError(record)

def build_sell_workers(account):
    sell_bot.sell(_L, account)


def build_buy_workers(account, assHand):
    for thread in range(gvars.MAX_WORKERS):  # this will launch the threads
        worker = 'th' + str(thread)  # establishing each worker name

        worker = threading.Thread(name=worker, target=buy_bot.buy, args=(_L, assHand, account))
        worker.start()  # it runs a run_tbot function, declared here as well

        time.sleep(1)


def main():
    set_logger_config()

    account, ass_and = set_alpaca_api_config()

    build_buy_workers(account, ass_and)
    build_sell_workers(account)


def set_alpaca_api_config():
    global alpaca_api
    # initialize the API with Alpaca
    alpaca_api = tradeapi.REST(gvars.API_KEY, gvars.API_SECRET_KEY, gvars.ALPACA_API_URL, api_version='v2')
    # initialize the asset handler
    assHand = AssetHandler()
    # get the Alpaca account ready
    try:
        _L.info("Getting account")
        tbot.check_account_ok(alpaca_api)  # check if it is ok to trade
        account = alpaca_api.get_account()
        tbot.clean_open_orders(alpaca_api)  # clean all the open orders
        _L.info("Got it")
    except Exception as e:
        _L.info(str(e))
    return account, assHand


def set_logger_config():
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


def is_market_about_to_close():
    # Figure out when the market will close so we can prepare to sell beforehand.
    clock = alpaca_api.get_clock()
    closing_time = clock.next_close.replace().timestamp()
    curr_time = clock.timestamp.replace().timestamp()
    time_to_close = closing_time - curr_time

    print(str(time_to_close) + " minutes til market close. " + tbot.display_time(time_to_close / 0.016667))

    if time_to_close < (60 * 60):
        # Close all positions when 60 minutes til market close.
        return True
    else:
        return False
