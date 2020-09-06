import mysql.connector

def getTickers():
    tickers = []
    try:
        sql = "select ticker from a1_ticker_table"
        conn = create_connection()
        c = conn.cursor()
        c.execute(sql)

        for column in c:
            tickers.append(str(column[0]))

        if c:
            c.close()
        if conn:
            conn.close()
    except mysql.connector.Error as err:
        print(err)

    return tickers

def getTicker(symbol):
    try:
        values = {'symbol': symbol}
        sql = "select ticker from a1_ticker_table where ticker=%(symbol)s and active=1"
        conn = create_connection()
        c = conn.cursor()
        c.execute(sql, values)

        for column in c:
            return str(column[0])

        if c:
            c.close()
        if conn:
            conn.close()
    except mysql.connector.Error as err:
        print(err)

    return None

def get_key_secrets(type):
    auth = []
    try:
        values = {'type': type}
        sql = "select api_url,api_key,api_secret from a4_alpaca_table where api_type=%(type)s"
        conn = create_connection()
        c = conn.cursor()
        c.execute(sql, values)

        for column in c:
            auth.append(str(column[0]))
            auth.append(str(column[1]))
            auth.append(str(column[2]))

        if c:
            c.close()
        if conn:
            conn.close()
    except mysql.connector.Error as err:
        print(err)

    return auth

def create_table(create_table_sql):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(create_table_sql)

        if conn:
            conn.close()
    except mysql.connector.Error as err:
        print(err)

def create_connection():
    try:
        cnx = mysql.connector.connect(user='root', password='root',
                                      host='localhost',
                                      database='stocks')
        return cnx
    except mysql.connector.Error as err:
        print(err)
    return

if __name__ == '__main__':
    get_key_secrets()

