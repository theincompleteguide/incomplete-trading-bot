from database import gvars
from other_functions import block_thread
from stocklib import Stock
from traderlib import Trader
import tulipy as ti
import os, time, threading, pytz


def get_rsi(trader=Trader, stock=Stock, loadHist=False):
    # this function calculates the RSI value

    trader._L.info('\n\n### RSI TREND ANALYSIS (%s for %s) ###' % (stock.name, stock.direction))

    while True:
        if loadHist:
            trader.load_historical_data(stock, interval=gvars.fetchItval['little'])

        # calculations
        rsi = ti.rsi(stock.df.close.values, 14)  # it uses 14 periods
        rsi = rsi[-1]

        if (stock.direction == gvars.BUY) and ((rsi > 50) and (rsi < 80)):
            trader._L.info('OK: RSI is %.2f' % rsi)
            return True, rsi

        elif (stock.direction == gvars.SELL) and ((rsi < 50) and (rsi > 20)):
            trader._L.info('OK: RSI is %.2f' % rsi)
            return True, rsi

        else:
            trader._L.info('RSI: %.0f, waiting (dir: %s)' % (rsi, stock.direction))

            trader.timeout += gvars.sleepTimes['RS']
            time.sleep(gvars.sleepTimes['RS'])
            return False
