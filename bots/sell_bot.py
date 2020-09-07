import logging
import threading

import tbot
from assetHandler import AssetHandler
from bots import bot
from indicators import general_trend, instant_trend, rsi_trend, stochastic_trend
from other_functions import block_thread
from stocklib import Stock
from traderlib import Trader, gvars, time


def sell(_L, account):
    # initialize trader object
    trader = Trader(gvars.API_KEY, gvars.API_SECRET_KEY, _L, account)

    while True:
        is_market_open = tbot.is_market_open(trader.alpaca)

        if is_market_open:
            try:
                positions = trader.alpaca.list_positions()
                for position in positions:
                    stock = Stock(position.symbol)
                    _L.info("Sell Position exist for Asset: {}".format(position.symbol))
                    start_sell_thread(stock, trader)

                time.sleep(30)
            except Exception as e:
                continue
        else:
            time.sleep(60)

            break


def start_sell_thread(stock, trader):
    worker = 'sell-thread-' + str(stock.name)  # establishing each worker name

    worker = threading.Thread(name=worker, target=process_asset_bought, args=(stock, trader))
    worker.start()  # it runs a run_tbot function, declared here as well


def process_asset_bought(stock, trader):
    ticker, lock = sell_run(trader, stock)  # run the trading program


def sell_run(trader=Trader, stock=Stock):
    # this is the main thread

    trader._L.info('\n\n\n # #  R U N N I N G  SELL B O T ––> (%s with %s) # #\n' % (stock.name, trader.thName))

    # 1. GENERAL TREND
    if not general_trend.get_general_trend(stock):  # check the trend
        return stock.name, True

    if stock != gvars.SELL:
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


if __name__ == '__main__':
    alpaca_api = gvars.get_alpaca_api()

    tbot.check_account_ok(alpaca_api)  # check if it is ok to trade
    account = alpaca_api.get_account()
    _L = logging.getLogger("demo")

    sell(_L, account)