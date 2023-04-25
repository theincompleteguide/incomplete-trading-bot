# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can find at www.theincompleteguide.com
# You will also find improvement ideas and explanations

from pathlib import Path
from datetime import datetime
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.common.enums import BaseURL


MAX_WORKERS = 10 # max threads at a time

gainRatio = 1.5 # takeProfit = -stopLoss*gainRatio
stopLossMargin = 0.05 # extra margin for the stop loss

operEquity = 10000 # defines the target amount per execution ($)
limitOrderMargin = 0.1 # percentage that defines the offset for the limit orders

# YOUR API KEYS AT ALPACA GO HERE!
API_KEY = "PKYCWW3124DHIFJOWMXP"
API_SECRET_KEY = "2dCo1QZB9JzaN9ZI1R6LyJFtUevLO98CraNlQ5JC"
ALPACA_API_URL = BaseURL.TRADING_PAPER

# this block checks whether you have your keys written or not
if API_KEY == "" or API_SECRET_KEY == "":
    print('\n\n##### \n\nPlease get an API key at the Alpaca website! \n\n##### \n\n')
    raise ValueError

################################################################ ATTEMPTS ->
# max iteration attempts for the different actions
maxAttempts = {
            'SO':5, # SUBMIT ORDER
            'CP':5, # CHECK POSITION
            'CO':5, # CANCEL ORDER
            'LHD1':10, # LOAD HISTORICAL DATA 1
            'LHD2':20 # LOAD HISTORICAL DATA 2
            }

# limit for the indicators
limStoch = {
            'maxBuy':75, # max allowed value to buy
            'minSell':25  # min allowed value to sell
            }

################################################################ TIMEFRAMES ->
# fetch historical data intervals
fetchItval = {
            'little': TimeFrame(5, TimeFrameUnit.Minute),
            'big': TimeFrame(30, TimeFrameUnit.Minute)
            }

# timeouts that will kill a process
timeouts = {
        'GT':0 # if 0, it discards a bad general trend instantly
        }

# waiting time before repeating each iteration
sleepTimes = {
                'GT': 10*60, # general trend
                'IT': 2*60, # instant trend
                'RS': 60, # RSI
                'ST': 60, # stochastic every minut
                'CO': 10, # check order every 10 seconds
                'SO': 5, # submit order every 5 seconds
                'LH': 5, # load_historical_data
                'PF': 10, # price fetch (current price)
                'CP': 10, # check position, to check if it entered
                'GS': 60, # get slope inside enter position
                'UA': 10*60 # unlock assets
                }

################################################################ PATHS ->
home = str(Path.home())

FILES_FOLDER = home + '/tbot_files_test/'
RAW_ASSETS = './_raw_assets.csv' # you should have this list at the same folder than everything
LOGS_PATH = FILES_FOLDER + 'logs/'
