import mysql.connector

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

