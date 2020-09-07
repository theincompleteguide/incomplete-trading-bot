from database import gvars
from other_functions import block_thread
from stocklib import Stock
from traderlib import Trader
import tulipy as ti
import os, time, threading, pytz


def get_stochastic(trader=Trader, stock=Stock, direction='', loadHist=False):
    # this function calculates the stochastic curves

    trader._L.info('\n\n### STOCHASTIC TREND ANALYSIS (%s for %s) ###' % (stock.name, stock.direction))

    try:
        while True:
            if loadHist:
                trader.load_historical_data(stock, interval=gvars.fetchItval['little'])

            # càlculs
            stoch_k_full, stoch_d_full = ti.stoch(
                stock.df.high.values,
                stock.df.low.values,
                stock.df.close.values,
                9, 6, 9)  # parameters for the curves
            stoch_k = stoch_k_full[-1]
            stoch_d = stoch_d_full[-1]

            # look for a buying condition
            if (
                    (direction == gvars.BUY) and
                    (stoch_k > stoch_d) and
                    ((stoch_k <= gvars.limStoch['maxBuy']) and (stoch_d <= gvars.limStoch['maxBuy']))
            ):
                trader._L.info('OK: k is over d: (K,D)=(%.2f,%.2f)' % (stoch_k, stoch_d))
                return True

            # look for a selling condition
            elif (
                    (direction == gvars.SELL) and
                    (stoch_k < stoch_d) and
                    ((stoch_d >= gvars.limStoch['minSell']) and (stoch_k >= gvars.limStoch['minSell']))
            ):
                trader._L.info('OK: k is under d: (K,D)=(%.2f,%.2f)' % (stoch_k, stoch_d))
                return True

            else:
                trader._L.info('NO: The stochastics are (K,D)=(%.2f,%.2f) for %s' % (stoch_k, stoch_d, direction))

                trader.timeout += gvars.sleepTimes['ST']
                time.sleep(gvars.sleepTimes['ST'])
                return False

    except Exception as e:
        trader._L.info('ERROR_GS: error when getting stochastics')
        trader._L.info(stock.df)
        trader._L.info(stock.direction)
        trader._L.info(str(e))
        return False
