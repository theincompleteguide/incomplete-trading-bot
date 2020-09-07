from datetime import time

import tbot
from bots import bot
from indicators import general_trend, instant_trend, rsi_trend, stochastic_trend
from other_functions import block_thread
from stocklib import Stock
from traderlib import Trader, gvars


def buy(_L, assHand, account):
    # initialize trader object
    trader = Trader(gvars.API_KEY, gvars.API_SECRET_KEY, _L, account)

    while True:
        market_about_to_close = bot.is_market_about_to_close()

        if market_about_to_close:
            ticker = assHand.find_target_asset()
            stock = Stock(ticker)

            try:
                res = trader.alpaca.get_position(ticker)
                assHand.lock_asset(ticker)
                continue
            except Exception as e:
                _L.info("Position not exist for Asset: {}".format(ticker))
                ticker = process_not_used_asset(assHand, stock, ticker, trader)
        else:
            _L.info("Market closing soon.  Closing positions.")
            tbot.clean_open_orders(trader.alpaca)

            _L.info("Market is closing soon. Ending all BUY...")
            break


def process_not_used_asset(assHand, stock, ticker, trader):
    ticker, lock = buy_run(trader, stock)  # run the trading program
    if lock:  # if the trend is not favorable, lock it temporarily
        assHand.lock_asset(ticker)
    else:
        assHand.make_asset_available(ticker)
    return ticker


def buy_run(trader=Trader, stock=Stock):
    # this is the main thread

    trader._L.info('\n\n\n # #  R U N N I N G   B O T ––> (%s with %s) # #\n' % (stock.name, trader.thName))

    if trader.check_position(stock, maxAttempts=2):  # check if the position exists beforehand
        trader._L.info('There is already a position open with %s, aborting!' % stock.name)
        return stock.name, True

    if not trader.is_tradable(stock.name):
        return stock.name, True

    # 1. GENERAL TREND
    # if not self.get_general_trend(stock):  # check the trend
    if not general_trend.get_general_trend(stock):  # check the trend
        return stock.name, True

    if stock != gvars.BUY:
        return stock.name, True

    if not trader.is_tradable(stock.name, stock.direction):  # can it be traded?
        return stock.name, True

    trader.timeout = 0
    while True:

        trader.load_historical_data(stock, interval=gvars.fetchItval['little'])

        # 2. INSTANT TREND
        if not instant_trend.get_instant_trend(stock):
            continue  # restart the loop

        # 3. RSI
        if not rsi_trend.get_rsi(stock):
            continue  # restart the loop

        # 4. STOCHASTIC
        if not stochastic_trend.get_stochastic(stock, direction=stock.direction):
            continue  # restart the loop

        currentPrice = trader.get_last_price(stock)
        sharesQty = trader.get_shares_from_equity(currentPrice)
        if not sharesQty:  # if no money left...
            continue  # restart the loop

        trader._L.info('%s %s stock at %.3f$' % (stock.direction, stock.name, currentPrice))

        orderDict = {
            'symbol': stock.name,
            'qty': sharesQty,
            'side': stock.direction,
            'type': 'limit',
            'limit_price': currentPrice
        }

        trader._L.info('[%s] Current price read: %.2f' % (stock.name, currentPrice))

        if not trader.submitOrder(orderDict):  # check if the order has been SENT
            trader._L.info('Could not submit order, RESTARTING SEQUENCE')
            return stock.name, False

        if not trader.check_position(stock):  # check if the order has EXISTS
            trader._L.info('Order did not become a position, cancelling order')
            trader.cancelOrder(trader.order.id)
            trader._L.info('Order cancelled correctly')
            return stock.name, False

        try:  # go on and enter the position
            trader.enter_position_mode(stock, currentPrice, sharesQty)
        except Exception as e:
            trader._L.info('ERROR_EP: error when entering position')
            trader._L.info(str(e))
            block_thread(trader._L, e, trader.thName, stock.name)

        trader._L.info('\n\n##### OPERATION COMPLETED #####\n\n')
        time.sleep(3)

        try:
            if 'YES' in trader.success:
                trader._L.info(trader.success)
                return stock.name, False
            else:
                trader._L.info('Blocking asset due to bad strategy')
                return stock.name, True
        except Exception as e:
            trader._L.info('ERROR_SU: failed to identify success')
            trader._L.info(str(e))
