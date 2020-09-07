from database import gvars
from other_functions import block_thread
from stocklib import Stock
from traderlib import Trader
import tulipy as ti
import os, time, threading, pytz


def get_general_trend(trader=Trader, stock=Stock):
    # this function analyses the general trend
    # it defines the direction and returns a True if defined

    trader._L.info('\n\n### GENERAL TREND ANALYSIS (%s) ###' % stock.name)
    timeout = 1

    try:
        while True:
            trader.load_historical_data(stock, interval=gvars.fetchItval['big'])

            # calculate the EMAs
            ema9 = ti.ema(stock.df.close.dropna().to_numpy(), 9)
            ema26 = ti.ema(stock.df.close.dropna().to_numpy(), 26)
            ema50 = ti.ema(stock.df.close.dropna().to_numpy(), 50)

            trader._L.info('[GT %s] Current: EMA9: %.3f // EMA26: %.3f // EMA50: %.3f' % (
                stock.name, ema9[-1], ema26[-1], ema50[-1]))

            # check the buying trend
            if (ema9[-1] > ema26[-1]) and (ema26[-1] > ema50[-1]):
                trader._L.info('OK: Trend going UP')
                stock.direction = gvars.BUY
                return True

            # check the selling trend
            elif (ema9[-1] < ema26[-1]) and (ema26[-1] < ema50[-1]):
                trader._L.info('OK: Trend going DOWN')
                stock.direction = gvars.SELL
                return True

            elif timeout >= gvars.timeouts['GT']:
                trader._L.info('This asset is not interesting (timeout)')
                return False

            else:
                trader._L.info('Trend not clear, waiting...')

                timeout += gvars.sleepTimes['GT']
                time.sleep(gvars.sleepTimes['GT'])

    except Exception as e:
        trader._L.info('ERROR_GT: error at general trend')
        trader._L.info(e)
        block_thread(trader._L, e, trader.thName)
