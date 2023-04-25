# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can find at www.theincompleteguide.com
# You will also find improvement ideas and explanations

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus, OrderSide, OrderType, TimeInForce
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

import tulipy as ti
import time, threading
import pytz

from datetime import datetime, timedelta, timezone
from other_functions import *
from math import ceil

class Trader:
    def __init__( self, API_KEY, API_SECRET_KEY, _L ):
        self._L = _L
        self.thName = threading.currentThread().getName()

        try:
            self.API_KEY = API_KEY
            self.API_SECRET_KEY = API_SECRET_KEY
            self.ALPACA_API_URL = gvars.ALPACA_API_URL
            self.alpaca = TradingClient( self.API_KEY, self.API_SECRET_KEY, url_override=self.ALPACA_API_URL ) # or use ENV Vars
            self.bars = StockHistoricalDataClient( self.API_KEY, self.API_SECRET_KEY )

        except Exception as e:
            self._L.info('ERROR_IN: error when initializing: ' + str(e))
            block_thread(self._L,e,self.thName)

        self.operEquity = gvars.operEquity
        self.pctMargin = gvars.limitOrderMargin/100

    def is_tradable(self,ticker,direction=False):
        # this function checks wether the asset is tradable
        # it may not be shortable. If so, the function locks it

        try:
            asset = self.alpaca.get_asset(ticker)
            if not asset.tradable:
                self._L.info('%s is not tradable, locking it' % ticker)
                return False
            else:
                if direction:
                    if (direction == OrderSide.SELL) and (not asset.shortable):
                        self._L.info('%s is not shortable, locking it' % ticker)
                        return False
                    elif (direction == OrderSide.BUY) and (not asset.tradable):
                        self._L.info('%s is not tradable, locking it' % ticker)
                        return False

                return True

        except:
            self._L.info('Asset %s not answering well' % ticker)
            pass

        self._L.info('%s is NOT tradable or something weird' % ticker)
        return False

    def announce_order(self):
        # this function acts as a visual aid

        self._L.info('#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#')
        self._L.info('#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#')
        self._L.info('#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#')
        self._L.info('# O R D E R   S U B M I T T E D       ')
        self._L.info('#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#')
        self._L.info('#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#')
        self._L.info('#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#')

    def set_stoploss(self,stopLoss,direction):
        #this function takes a price as a input and sets the stoploss there

        try:
            if direction == OrderSide.BUY:
                self.stopLoss = float(stopLoss - stopLoss*gvars.stopLossMargin)
            elif direction == OrderSide.SELL:
                self.stopLoss = float(stopLoss + stopLoss*gvars.stopLossMargin)
            else:
                raise ValueError
        except Exception as e:
            self._L.info('ERROR_SL! Direction was not clear when setting stoploss!')
            self._L.info(str(e))
            self.stopLoss = float(stopLoss)

        self._L.info('StopLoss set at %.2f' % self.stopLoss)

        return self.stopLoss

    def set_takeprofit(self,entryPrice,stopLoss):
        # this function takes the stoploss and sets the take profit
        # depending on the gainRatio defined at the gvars file

        diff = entryPrice - stopLoss
        try:
            self.takeProfit = round(entryPrice + diff*gvars.gainRatio,2)
            # long: if I enter at 10$ with stop loss at 8$, take profit = 10$ + (10$-8$)*2 = 14
            # short: if I enter at 10$ with stop loss at 12$, take profit = 10$ + (10$-12$)*2 = 6
        except Exception as e:
            self._L.info('ERROR_TP! Direction was not clear when setting stoploss!')
            self._L.info(e)
            self.takeProfit = round(entryPrice + diff*1.5,2)

        return self.takeProfit

    def get_shares_from_equity(self,assetPrice):
        # this function returns the number of shares achievable with the purchasing power

        account = self.alpaca.get_account()
        if float(account.buying_power) < self.operEquity:
            self._L.info('Oops! Not enough buying power (%d$), aborting' % float(account.buying_power))
            time.sleep(3)
            return False
        else:
            sharesQty = int(self.operEquity/assetPrice)
            return sharesQty

    def load_historical_data( self, stock, interval=TimeFrame.Minute, limit=100 ):
        # this function fetches the data from Alpaca
        # it is important to check whether is updated or not

        timedeltaItv = ceil( interval.amount * 1.5) # 150% de l'interval, per si de cas

        limit += 1  # to retrieve all the amount of data we want

        attempt = 1
        while True:
            try: # fetch the data
                if interval.value == '30Min':
                    interval = TimeFrame(5, TimeFrameUnit.Minute)  # 5 minutes
                    start_time = datetime.now( timezone.utc ) - timedelta( minutes = interval.amount * limit )  # to retrieve the latest data
                    bars_params = StockBarsRequest( symbol_or_symbols=stock.name, timeframe=interval, limit=limit, start=start_time )
                    df = self.bars.get_stock_bars( bars_params ).df.reset_index( level=['symbol'] )
                    stock.df = df.resample('30min').agg({
                                        'open':'first',
                                        'high':'max',
                                        'low':'min',
                                        'close':'last',
                                        'volume':'sum'
                                        })

                else:
                    start_time = datetime.now( timezone.utc ) - timedelta( minutes = interval.amount * limit )  # to retrieve the latest data
                    bars_params = StockBarsRequest( symbol_or_symbols=stock.name, timeframe=interval, limit=limit, start=start_time )
                    stock.df = self.bars.get_stock_bars( bars_params ).df.reset_index( level=['symbol'] )

            except Exception as e:
                self._L.info('WARNING_HD: Could not load historical data, retrying')
                self._L.info(e)
                time.sleep(gvars.sleepTimes['LH'])

            try: # check if the data is updated

                lastEntry = stock.df.index[-1]  # last timestamp entry
                lastEntry = lastEntry.tz_convert('utc')
                nowTimeDelta = datetime.now(timezone.utc) # ara - 5min

                diff = ( nowTimeDelta.replace(tzinfo=None) - lastEntry.replace(tzinfo=None) ).total_seconds()
                diff = int(abs(diff)/60) # min
                if diff <= timedeltaItv:
                    stock.lastTimeStamp = lastEntry
                    return stock.df
                else:
                    if gvars.maxAttempts['LHD1'] <= attempt <= gvars.maxAttempts['LHD2']:
                        self._L.info('Fetching data, but it is taking a while (%d)...' % attempt)
                        self._L.info('Last entry    : ' + str(lastEntry))
                        self._L.info('Current time  : ' + str(nowTimeDelta))
                        self._L.info('Diff          : ' + str(diff))
                        self._L.info('Interval      : ' + str(interval))

                    elif attempt > gvars.maxAttempts['LHD2']:
                        self._L.info('WARNING_FD! Max attempts (%d) reached trying to pull data, slowing down...' % attempt)
                        time.sleep(gvars.sleepTimes['LH']*4)

                    time.sleep(gvars.sleepTimes['LH'])
                    attempt += 1

            except Exception as e:
                self._L.info('ERROR_CD: Could not check if data is updated')
                self._L.info(str(e))
                time.sleep(gvars.sleepTimes['LH'])

    def get_open_positions(self, assetId):
        # this function checks wether you already have an open position with the asset

        positions = self.alpaca.get_all_positions()
        for position in positions:
            if position.symbol == assetId:
                return position.count(position.symbol)
            else:
                return False

    def submitOrder(self,orderDict):
        # this is a custom function, that secures the submission
        # order dict contains the order information

        self.announce_order()

        side = orderDict['side']
        symbol = orderDict['symbol']
        qty = orderDict['qty']
        type = orderDict['type']
        time_in_force = TimeInForce.GTC

        if type == OrderType.LIMIT: # adjust order for a limit type
            self._L.info('Desired limit price for limit order: %.3f$' % orderDict['limit_price'])

            if side == OrderSide.BUY:
                limit_price = orderDict['limit_price'] * (1+self.pctMargin)
                # this line modifies the price that comes from the orderDict
                # adding the needed flexibility for making sure the order goes through
            elif side == OrderSide.SELL:
                limit_price = orderDict['limit_price'] * (1-self.pctMargin)
            else:
                self._L.info('Side not identified: ' + str(side))
                block_thread(self._L,e,self.thName)

            if limit_price >= 1: limit_price = round( limit_price, 2 )  # based on api documentation
            else: limit_price = round( limit_price, 4 )                 # ( https://alpaca.markets/docs/trading/orders/#limit-order )

            self._L.info('Corrected (added margin) limit price: %.3f$' % limit_price)

        elif type == OrderType.MARKET: # adjust order for a market type
            self._L.info('Desired limit price for market order: %.3f$' % orderDict['limit_price'])


        attempt = 0
        while attempt < gvars.maxAttempts['SO']:
            try:
                if type == OrderType.LIMIT:
                    order_request = LimitOrderRequest(
                                        side = side,
                                        qty = qty,
                                        type = type,
                                        time_in_force = time_in_force,
                                        symbol = symbol,
                                        limit_price = limit_price )
                    self.order = self.alpaca.submit_order( order_request )

                    self._L.info("Limit order of | %d %s %s | submitted" % (qty,symbol,side))
                    self._L.info(self.order)
                    return True

                elif type == OrderType.MARKET:
                    order_request = MarketOrderRequest(
                                        side = side,
                                        qty = qty,
                                        type = type,
                                        time_in_force = time_in_force,
                                        symbol = symbol )
                    self.order = self.alpaca.submit_order( order_request )

                    self._L.info("Market order of | %d %s %s | submitted" % (qty,symbol,side))
                    self._L.info(self.order)
                    return True

            except Exception as e:
                self._L.info('WARNING_EO: order of | %d %s %s | did not enter' % (qty,symbol,side))
                self._L.info(str(e))
                time.sleep(gvars.sleepTimes['SO'])
                attempt += 1

        self._L.info('WARNING_SO: Could not submit the order, aborting (submitOrder)')
        return False

    def cancelOrder(self,orderId):
        # this is a custom function, that secures the cancelation

        attempt = 0
        while attempt < gvars.maxAttempts['CO']:
            try:
                orders_filter = GetOrdersRequest( status = QueryOrderStatus.ALL, limit = 100 )
                ordersList = self.alpaca.get_orders( orders_filter )

                # find the order ID and the closed status, check it matches
                for order in ordersList:
                    if order.id == orderId:
                        self._L.info('Cancelling order for ' + order.symbol)
                        self.alpaca.cancel_order_by_id( order.id )
                        return True
            except Exception as e:
                self._L.info('WARNING_CO! Failed to cancel order, trying again')
                self._L.info(e)
                self._L.info(str(ordersList))
                attempt += 1

                time.sleep(5)

        self._L.info('DANGER: order could not be cancelled, blocking thread')
        block_thread(self._L,e,self.thName,stock.name)

    def check_position(self,stock,maxAttempts=False):
        # this function checks whether the position is there or not

        if not maxAttempts:
            maxAttempts = gvars.maxAttempts['CP']

        attempt = 0
        while attempt < maxAttempts:
            try:
                position = self.alpaca.get_open_position(stock.name)
                stock.avg_entry_price = float(position.avg_entry_price)
                stock.currentPrice = float(self.alpaca.get_open_position(stock.name).current_price)
                return True
            except:
                time.sleep(gvars.sleepTimes['CP'])
                attempt += 1

        self._L.info('Position NOT found for %s' % stock.name)
        return False

    def get_general_trend(self,stock):
        # this function analyses the general trend
        # it defines the direction and returns a True if defined

        self._L.info('\n\n### GENERAL TREND ANALYSIS (%s) ###' % stock.name)
        timeout = 1

        try:
            while True:
                self.load_historical_data(stock,interval=gvars.fetchItval['big'])

                # calculate the EMAs
                ema9 = ti.ema(stock.df.close.dropna().to_numpy(), 9)
                ema26 = ti.ema(stock.df.close.dropna().to_numpy(), 26)
                ema50 = ti.ema(stock.df.close.dropna().to_numpy(), 50)

                self._L.info('[GT %s] Current: EMA9: %.3f // EMA26: %.3f // EMA50: %.3f' % (stock.name,ema9[-1],ema26[-1],ema50[-1]))

                # check the buying trend
                if (ema9[-1] > ema26[-1]) and (ema26[-1] > ema50[-1]):
                    self._L.info('OK: Trend going UP')
                    stock.direction = OrderSide.BUY
                    return True

                # check the selling trend
                elif (ema9[-1] < ema26[-1]) and (ema26[-1] < ema50[-1]):
                    self._L.info('OK: Trend going DOWN')
                    stock.direction = OrderSide.SELL
                    return True

                elif timeout >= gvars.timeouts['GT']:
                    self._L.info('This asset is not interesting (timeout)')
                    return False

                else:
                    self._L.info('Trend not clear, waiting...')

                    timeout += gvars.sleepTimes['GT']
                    time.sleep(gvars.sleepTimes['GT'])

        except Exception as e:
            self._L.info('ERROR_GT: error at general trend')
            self._L.info(e)
            block_thread(self._L,e,self.thName)

    def get_last_price(self,stock):
        # this function fetches the last full 1-min candle of Alpaca in a loop

        while True:
            try:
                lastPrice = self.load_historical_data( stock, interval=TimeFrame.Minute, limit=1 )
                stock.lastPrice = float(lastPrice.close)
                self._L.info('Last price read ALPACA    : ' + str(stock.lastPrice))
                return stock.lastPrice
            except:
                self._L.info('Failed to fetch data from alpaca, trying again')
                time.sleep(10)

    def get_instant_trend(self,stock,loadHist=False,wait=True):
        # this function analyses the instant trend
        # it checks the direction and returns a True if it matches

        self._L.info('\n\n### INSTANT TREND ANALYSIS (%s for %s) ###' % (stock.name,stock.direction))

        try:
            while True:
                if loadHist:
                    self.load_historical_data(stock,interval=gvars.fetchItval['little'])

                # calculate the EMAs
                ema9 = ti.ema(stock.df.close.dropna().to_numpy(), 9)
                ema26 = ti.ema(stock.df.close.dropna().to_numpy(), 26)
                ema50 = ti.ema(stock.df.close.dropna().to_numpy(), 50)

                self._L.info('[%s] Instant Trend EMAS = [%.2f,%.2f,%.2f]' % (stock.name,ema9[-1],ema26[-1],ema50[-1]))

                # look for a buying trend
                if (
                        (stock.direction == OrderSide.BUY) and
                        (ema9[-1] > ema26[-1]) and
                        (ema26[-1] > ema50[-1])
                    ):
                    self._L.info('OK: Trend going UP')
                    return True

                # look for a selling trend
                elif (
                        (stock.direction == OrderSide.SELL) and
                        (ema9[-1] < ema26[-1]) and
                        (ema26[-1] < ema50[-1])
                    ):
                    self._L.info('OK: Trend going DOWN')
                    return True

                else:
                    self._L.info('Trend not clear, waiting (%s)' % stock.direction)

                    if wait:
                        self.timeout += gvars.sleepTimes['IT']
                        time.sleep(gvars.sleepTimes['IT'])

                    return False

        except Exception as e:
            self._L.info('ERROR_IT: error at instant trend')
            self._L.info(e)
            block_thread(self._L,e,self.thName)

    def get_rsi(self,stock,loadHist=False):
        # this function calculates the RSI value

        self._L.info('\n\n### RSI TREND ANALYSIS (%s for %s) ###' % (stock.name,stock.direction))

        while True:
            if loadHist:
                self.load_historical_data(stock,interval=gvars.fetchItval['little'])

            # calculations
            rsi = ti.rsi(stock.df.close.values, 14) # it uses 14 periods
            rsi = rsi[-1]

            if (stock.direction == OrderSide.BUY) and ((rsi>50) and (rsi<80)):
                self._L.info('OK: RSI is %.2f' % rsi)
                return True,rsi

            elif (stock.direction == OrderSide.SELL) and ((rsi<50) and (rsi>20)):
                self._L.info('OK: RSI is %.2f' % rsi)
                return True,rsi

            else:
                self._L.info('RSI: %.0f, waiting (dir: %s)' % (rsi,stock.direction))

                self.timeout += gvars.sleepTimes['RS']
                time.sleep(gvars.sleepTimes['RS'])
                return False

    def get_stochastic(self,stock,direction,loadHist=False):
        # this function calculates the stochastic curves

        self._L.info('\n\n### STOCHASTIC TREND ANALYSIS (%s for %s) ###' % (stock.name,stock.direction))


        try:
            while True:
                if loadHist:
                    self.load_historical_data(stock,interval=gvars.fetchItval['little'])

                # càlculs
                stoch_k_full, stoch_d_full = ti.stoch(
                                    stock.df.high.values,
                                    stock.df.low.values,
                                    stock.df.close.values,
                                    9, 6, 9) # parameters for the curves
                stoch_k = stoch_k_full[-1]
                stoch_d = stoch_d_full[-1]

                # look for a buying condition
                if (
                        (direction == OrderSide.BUY) and
                        (stoch_k > stoch_d) and
                        ((stoch_k <= gvars.limStoch['maxBuy']) and (stoch_d <= gvars.limStoch['maxBuy']))
                    ):
                    self._L.info('OK: k is over d: (K,D)=(%.2f,%.2f)' % (stoch_k,stoch_d))
                    return True

                # look for a selling condition
                elif (
                        (direction == OrderSide.SELL) and
                        (stoch_k < stoch_d) and
                        ((stoch_d >= gvars.limStoch['minSell']) and (stoch_k >= gvars.limStoch['minSell']))
                    ):
                    self._L.info('OK: k is under d: (K,D)=(%.2f,%.2f)' % (stoch_k,stoch_d))
                    return True

                else:
                    self._L.info('NO: The stochastics are (K,D)=(%.2f,%.2f) for %s' % (stoch_k,stoch_d,direction))

                    self.timeout += gvars.sleepTimes['ST']
                    time.sleep(gvars.sleepTimes['ST'])
                    return False

        except Exception as e:
            self._L.info('ERROR_GS: error when getting stochastics')
            self._L.info(stock.df)
            self._L.info(stock.direction)
            self._L.info(str(e))
            return False

    def enter_position_mode(self,stock,desiredPrice,sharesQty):
        # this function holds a loop taking care of the open position
        # it is constantly checking the conditions to exit

        self._L.info('Position entered')

        stock.avg_entry_price = float(self.alpaca.get_open_position(stock.name).avg_entry_price)
        ema50 = ti.ema(stock.df.close.dropna().to_numpy(), 50)
        stopLoss = self.set_stoploss(ema50,direction=stock.direction) # stoploss = EMA50
        takeProfit = self.set_takeprofit(stock.avg_entry_price,stopLoss)

        if stock.direction == OrderSide.BUY:
            targetGainInit = int((takeProfit-stock.avg_entry_price) * sharesQty)
            reverseDirection = OrderSide.SELL

        elif stock.direction == OrderSide.SELL:
            targetGainInit = int((stock.avg_entry_price-takeProfit) * sharesQty)
            reverseDirection = OrderSide.BUY

        self._L.info('######################################')
        self._L.info('#    TICKER       : %s'       % stock.name)
        self._L.info('#    SIDE         : %s'       % stock.direction)
        self._L.info('#    QTY          : %d'       % sharesQty)
        self._L.info('#    TARGET GAIN  : %.3f$'    % targetGainInit)
        self._L.info('#    TAKE PROFIT  : %.3f$'    % takeProfit)
        self._L.info('#    DESIRED ENTRY: %.3f$'    % desiredPrice)
        self._L.info('#    AVG ENTRY    : %.3f$'    % stock.avg_entry_price)
        self._L.info('#    STOP LOSS    : %.3f$'    % stopLoss)
        self._L.info('######################################\n\n')

        timeout = 0
        stochTurn = 0
        stochCrossed = False
        exitSignal = False

        while True:

            targetGain = targetGainInit

            # not at every iteration it will check every condition
            # some of them can wait
            if (stochTurn >= gvars.sleepTimes['GS']) or (timeout == 0):

                # check the stochastic crossing
                stochTurn = 0
                self.load_historical_data(stock,interval=gvars.fetchItval['little'])
                stochCrossed = self.get_stochastic(stock,direction=reverseDirection)

            # check if the position exists and load the price at stock.currentPrice
            if not self.check_position(stock):
                self._L.info('Warning! Position not found at Alpaca')
                return False
            else:
                currentPrice = stock.currentPrice

            # calculate current gain
            if stock.direction == OrderSide.BUY:
                currentGain = (currentPrice - stock.avg_entry_price) * sharesQty
            elif stock.direction == OrderSide.SELL:
                currentGain = (stock.avg_entry_price - currentPrice) * sharesQty


            # if stop loss reached
            if (
                    (stock.direction == OrderSide.BUY and currentPrice <= stopLoss) or
                    (stock.direction == OrderSide.SELL and currentPrice >= stopLoss)
                ):
                self._L.info('STOPLOSS reached at price %.3f' % currentPrice)
                self.success = 'NO: STOPLOSS'
                break # break the while loop

            # if take profit reached
            elif currentGain >= targetGain:
                self._L.info('# Target gain reached at %.3f. BYE   #' % currentPrice)
                self.success = 'YES: TGT GAIN'
                break # break the while loop

            # if stochastics crossed otherwise
            elif stochCrossed:
                self.success = 'YES: STOCH XED WITH GAIN'
                break # break the while loop

            else:
                self._L.info('%s: %.2f <-- %.2f$ --> %.2f$ (gain: %.2f$)' % (stock.name,stopLoss,currentPrice,takeProfit,currentGain))

                time.sleep(gvars.sleepTimes['PF'])
                timeout += gvars.sleepTimes['PF']
                stochTurn += gvars.sleepTimes['PF']

        # get out!
        orderOut = False
        while not orderOut:
            orderDict = {
                        'side':reverseDirection,
                        'symbol':stock.name,
                        'type':OrderType.MARKET, # it is a MARKET order, now
                        'limit_price':currentPrice,
                        'qty':sharesQty
                        }

            orderOut = self.submitOrder(orderDict)

        self._L.info('%i %s %s at %.2f DONE' % (sharesQty, stock.name, stock.direction, currentPrice))

        return True

    ################## RUN ##################
    def run(self,stock):
        # this is the main thread

        self._L.info('\n\n\n # #  R U N N I N G   B O T --> (%s with %s) # #\n' % (stock.name,self.thName))

        if self.check_position(stock,maxAttempts=2): # check if the position exists beforehand
            self._L.info('There is already a position open with %s, aborting!' % stock.name)
            return stock.name,True

        if not self.is_tradable(stock.name):
            return stock.name,True

        # 1. GENERAL TREND
        if not self.get_general_trend(stock): # check the trend
            return stock.name,True

        if not self.is_tradable(stock.name,stock.direction): # can it be traded?
            return stock.name,True

        self.timeout = 0
        while True:

            self.load_historical_data(stock,interval=gvars.fetchItval['little'])

            # 2. INSTANT TREND
            if not self.get_instant_trend(stock):
                continue # restart the loop

            # 3. RSI
            if not self.get_rsi(stock):
                continue # restart the loop

            # 4. STOCHASTIC
            if not self.get_stochastic(stock,direction=stock.direction):
                continue # restart the loop

            currentPrice = self.get_last_price(stock)
            sharesQty = self.get_shares_from_equity(currentPrice)
            if not sharesQty: # if no money left...
                continue # restart the loop

            self._L.info('%s %s stock at %.3f$' % (stock.direction,stock.name,currentPrice))

            orderDict = {
                        'symbol':stock.name,
                        'qty':sharesQty,
                        'side':stock.direction,
                        'type':OrderType.LIMIT,
                        'limit_price':currentPrice
                        }

            self._L.info('[%s] Current price read: %.2f' % (stock.name,currentPrice))

            if not self.submitOrder(orderDict): # check if the order has been SENT
                self._L.info('Could not submit order, RESTARTING SEQUENCE')
                return stock.name,False

            if not self.check_position(stock): # check if the order has EXISTS
                self._L.info('Order did not become a position, cancelling order')
                self.cancelOrder(self.order.id)
                self._L.info('Order cancelled correctly')
                return stock.name,False

            try: # go on and enter the position
                self.enter_position_mode(stock,currentPrice,sharesQty)
            except Exception as e:
                self._L.info('ERROR_EP: error when entering position')
                self._L.info(str(e))
                block_thread(self._L,e,self.thName,stock.name)

            self._L.info('\n\n##### OPERATION COMPLETED #####\n\n')
            time.sleep(3)

            try:
                if 'YES' in self.success:
                    self._L.info(self.success)
                    return stock.name,False
                else:
                    self._L.info('Blocking asset due to bad strategy')
                    return stock.name,True
            except Exception as e:
                self._L.info('ERROR_SU: failed to identify success')
                self._L.info(str(e))
