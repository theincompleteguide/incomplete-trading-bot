import logging
import threading

import tbot
from assetHandler import AssetHandler
from bots import bot
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
                    print("Sell Position exist for Asset: {}".format(position.symbol))
                    process_asset_bought(stock, trader)
            except Exception as e:
                continue
        else:
            time.sleep(60)

            break


def process_asset_bought(stock, trader):
    ticker, lock = trader.sell_run(stock)  # run the trading program


if __name__ == '__main__':
    alpaca_api = gvars.get_alpaca_api()

    tbot.check_account_ok(alpaca_api)  # check if it is ok to trade
    account = alpaca_api.get_account()
    _L = logging.getLogger("demo")

    sell(_L, account)