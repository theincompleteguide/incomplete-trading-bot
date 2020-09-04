import pandas_datareader as pdr
import datetime

ticker = "MSFT"

ohlcv = pdr.get_data_yahoo(ticker,
                           datetime.date.today()-datetime.timedelta(1825),
                           datetime.date.today())

df = ohlcv.copy()