from datetime import datetime

import mysql

import databaseMySql
import gvars
import alpaca_trade_api as tradeapi

def updateTickerIfItsNew():
    conn = databaseMySql.create_connection()

    try:
        cur = conn.cursor()

        sql = "select ticker from a1_ticker_table where description is null"
        cur.execute(sql)

        rows = cur.fetchall()
        for row in rows:
            setCompanyDetails(str(row[0]))

        if cur:
            cur.close()
    except mysql.connector.Error as e:
        print(e)

    if conn:
        conn.close()

def setCompanyDetails(symbol):
    polygon = tradeapi.polygon.rest.REST(gvars.API_LIVE_KEY,
                                         'staging' in gvars.ALPACA_API_URL)

    try:
        companyDetails = polygon.company(symbol)

        if companyDetails is None:
            print("Got empty result for {}".format(symbol))
        else:
            industry = buildField(companyDetails, 'industry')
            sector = buildField(companyDetails, 'sector')
            description = buildField(companyDetails, 'description')
            exchange = buildField(companyDetails, 'exchange')
            exchangeSymbol = buildField(companyDetails, 'exchangeSymbol')
            tags = str(buildField(companyDetails, 'tags'))
            type = buildField(companyDetails, 'type')
            country = buildField(companyDetails, 'country')
            hq_country = buildField(companyDetails, 'hq_country')
            hq_state = buildField(companyDetails, 'hq_state')
            active = buildField(companyDetails, 'active')

            if len(description) > 999:
                description = description[:999]
            if len(tags) > 39:
                tags = tags[:39]
            tags = tags.replace("'", "")
            tags = tags.replace("[", "")
            tags = tags.replace("]", "")

            values = {
                     'industry':industry,
                     'sector':sector,
                     'description':description,
                     'exchange':exchange,
                     'exchangeSymbol':exchangeSymbol,
                     'tags':tags,
                     'type':type,
                     'country':country,
                     'hq_country':hq_country,
                     'hq_state':hq_state,
                     'active':active,
                     'symbol':symbol
                     }

            sql = "update a1_ticker_table set " \
                  "industry=%(industry)s," \
                  "sector=%(sector)s," \
                  "description=%(description)s," \
                  "exchange=%(exchange)s," \
                  "exchangeSymbol=%(exchangeSymbol)s," \
                  "tags=%(tags)s," \
                  "type=%(type)s," \
                  "country=%(country)s," \
                  "hq_country=%(hq_country)s," \
                  "hq_state=%(hq_state)s," \
                  "active=%(active)s " \
                  "where ticker=%(symbol)s"
            updateField(sql, values)

            print("Company details for {} ".format(symbol), values)
    except Exception as sim_exc:
        print("Got exception for {} ".format(symbol),sim_exc)


def buildField(companyDetails, field):
    try:
        return companyDetails._raw[field]
    except Exception as sim_exc:
        return ""

def updateField(sql, values):
    print(values)
    conn = databaseMySql.create_connection()
    cur = conn.cursor()
    cur.execute(sql, values)
    conn.commit()

    if cur:
        cur.close()
    if conn:
        conn.close()


def updateAllTickers():
    tickers = databaseMySql.getTickers()
    for ticker in tickers:
        setCompanyDetails(ticker)


if __name__ == '__main__':
    authLive = databaseMySql.get_key_secrets('LIVE')
    auth     = databaseMySql.get_key_secrets('PAPER')

    gvars.ALPACA_API_URL = auth[0]
    gvars.API_KEY        = auth[1]
    gvars.API_SECRET_KEY = auth[2]
    gvars.API_LIVE_KEY   = authLive[1]

    # updateAllTickers()

    updateTickerIfItsNew()