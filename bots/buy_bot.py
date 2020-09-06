import tbot
from bots import bot
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
    ticker, lock = trader.buy_run(stock)  # run the trading program
    if lock:  # if the trend is not favorable, lock it temporarily
        assHand.lock_asset(ticker)
    else:
        assHand.make_asset_available(ticker)
    return ticker