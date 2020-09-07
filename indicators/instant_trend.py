from database import gvars
from other_functions import block_thread
from stocklib import Stock
from traderlib import Trader
import tulipy as ti
import os, time, threading, pytz


def get_instant_trend(trader=Trader, stock=Stock, loadHist=False, wait=True):
    # this function analyses the instant trend
    # it checks the direction and returns a True if it matches

    trader._L.info('\n\n### INSTANT TREND ANALYSIS (%s for %s) ###' % (stock.name, stock.direction))

    try:
        while True:
            if loadHist:
                trader.load_historical_data(stock, interval=gvars.fetchItval['little'])

            # calculate the EMAs
            ema9 = ti.ema(stock.df.close.dropna().to_numpy(), 9)
            ema26 = ti.ema(stock.df.close.dropna().to_numpy(), 26)
            ema50 = ti.ema(stock.df.close.dropna().to_numpy(), 50)

            trader._L.info(
                '[%s] Instant Trend EMAS = [%.2f,%.2f,%.2f]' % (stock.name, ema9[-1], ema26[-1], ema50[-1]))

            # look for a buying trend
            if (
                    (stock.direction == gvars.BUY) and
                    (ema9[-1] > ema26[-1]) and
                    (ema26[-1] > ema50[-1])
            ):
                trader._L.info('OK: Trend going UP')
                return True

            # look for a selling trend
            elif (
                    (stock.direction == gvars.SELL) and
                    (ema9[-1] < ema26[-1]) and
                    (ema26[-1] < ema50[-1])
            ):
                trader._L.info('OK: Trend going DOWN')
                return True

            else:
                trader._L.info('Trend not clear, waiting (%s)' % stock.direction)

                if wait:
                    trader.timeout += gvars.sleepTimes['IT']
                    time.sleep(gvars.sleepTimes['IT'])

                return False

    except Exception as e:
        trader._L.info('ERROR_IT: error at instant trend')
        trader._L.info(e)
        block_thread(trader._L, e, trader.thName)
