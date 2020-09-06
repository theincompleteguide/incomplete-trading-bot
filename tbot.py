# encoding: utf-8

import logging

# This code is free, THANK YOU!
# It is explained at the guide you can find at www.theincompleteguide.com
# You will also find improvement ideas and explanations
from database import databaseMySql
from alpaca_trade_api import rest
from stocklib import *
from traderlib import *
from other_functions import *

# Global object we log to; the handler will work with any log message
from stocklib import Stock
from traderlib import Trader

_L = logging.getLogger("demo")

alpaca_api = None


def clean_open_orders(api):
    # First, cancel any existing orders so they don't impact our buying power.
    orders = api.list_orders(status="open")

    print('\nCLEAR ORDERS')
    print('%i orders were found open' % int(len(orders)))

    for order in orders:
        api.cancel_order(order.id)


def check_account_ok(api):
    account = api.get_account()
    if account.account_blocked or account.trading_blocked or account.transfers_blocked:
        print('OJO, account blocked. Ooops!!!')
        import pdb;
        pdb.set_trace()


def is_market_open(api):
    is_open = api.get_clock().is_open
    if not is_open:
        clock = api.get_clock()
        opening_time = clock.next_open.replace().timestamp()
        curr_time = clock.timestamp.replace().timestamp()
        time_to_open = int((opening_time - curr_time) / 60)

        print(str(time_to_open) + " minutes til market open. " + display_time(time_to_open / 0.016667))

    return is_open


intervals = (
    ('days', 86400),  # 60 * 60 * 24
    ('hours', 3600),  # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


if __name__ == '__main__':
    alpaca_api = gvars.get_alpaca_api()

    # if is_market_open():
    # bot.main()
