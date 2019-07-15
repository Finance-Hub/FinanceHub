import pandas as pd
from time import time
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from trackers import SingleNameEquity, BondFutureTracker, FXForwardTrackers

# ===== DATABASE CONNECTION =====
connect_dict = {'flavor': 'postgres+psycopg2',
                'database': '[DATABASE NAME]',
                'schema': '[DATABASE SCHEMA]',
                'user': '[USERNAME]',
                'password': '[PASSWORD]',
                'host': '[HOST ADDRESS]',
                'port': '[PORT NUMBER]'}


db_connect = create_engine("{flavor}://{username}:{password}@{host}:{port}/{database}"
                           .format(host=connect_dict['host'],
                                   database=connect_dict['database'],
                                   username=connect_dict['user'],
                                   password=connect_dict['password'],
                                   port=connect_dict['port'],
                                   flavor=connect_dict['flavor']))


# ===============================
# ===== EQUITY SINGLE NAMES =====
# ===============================
stocks = ['PETR4 BZ Equity',
          'BBDC4 BZ Equity',
          'VIVT4 BZ Equity',
          'ITUB4 BZ Equity',
          'VALE3 BZ Equity',
          'ABEV3 BZ Equity',
          'BBAS3 BZ Equity',
          'LREN3 BZ Equity',
          'RAIL3 BZ Equity',
          'SUZB3 BZ Equity',
          'RENT3 BZ Equity',
          'AAPL US Equity',
          'IBM US Equity',
          'GOOGL US Equity',
          'VZ US Equity',
          'AXP US Equity',
          'JPM US Equity',
          'KO US Equity',
          'XOM US Equity',
          'GE US Equity',
          'C US Equity',
          'BAC US Equity']

for ss in stocks:
    print(ss)
    start = time()

    sne = SingleNameEquity(ss)

    # uploads the metadata
    try:
        sne.df_metadata.to_sql('trackers_description', con=db_connect, index=False, if_exists='append')
    except IntegrityError:
        pass

    # erase the old tracker
    sql_query = f"DELETE FROM trackers WHERE fh_ticker IN ('{sne.fh_ticker}')"
    conn = db_connect.raw_connection()
    cursor = conn.cursor()
    cursor.execute(sql_query)
    conn.commit()
    cursor.close()

    # upload new tracker - pandas method
    try:
        sne.df_tracker.to_sql('trackers', con=db_connect, index=False, if_exists='append', method='multi')
    except IntegrityError:
        pass

    print(round((time() - start)), 'seconds to upload')

# ========================
# ===== BOND FUTURES =====
# ========================
countries = ['US', 'DE', 'FR', 'IT', 'JP', 'AU', 'GB', 'CA']

for country in countries:
    print(country)
    start = time()

    bf = BondFutureTracker(country=country, start_date='1980-01-01', end_date=pd.to_datetime('today'))

    # uploads the metadata
    try:
        bf.df_metadata.to_sql('trackers_description', con=db_connect, index=False, if_exists='append')
    except IntegrityError:
        pass

    # erase the old tracker
    sql_query = f"DELETE FROM trackers WHERE fh_ticker IN ('{bf.fh_ticker}')"
    conn = db_connect.raw_connection()
    cursor = conn.cursor()
    cursor.execute(sql_query)
    conn.commit()
    cursor.close()

    # upload new tracker - pandas method
    try:
        bf.df_tracker.to_sql('trackers', con=db_connect, index=False, if_exists='append', method='multi')
    except IntegrityError:
        pass

    print(round((time() - start)), 'seconds to upload')


# ==============
# ===== FX =====
# ==============
currencies = ['AUD', 'BRL', 'CAD', 'CHF', 'CLP', 'CZK', 'EUR', 'GBP', 'HUF', 'JPY', 'KRW',
              'MXN', 'NOK', 'NZD', 'PHP', 'PLN', 'SEK', 'SGD', 'TRY', 'TWD', 'ZAR']

for curr in currencies:
    print(curr)
    start = time()

    fx = FXForwardTrackers(curr)

    # uploads the metadata
    try:
        fx.df_metadata.to_sql('trackers_description', con=db_connect, index=False, if_exists='append')
    except IntegrityError:
        pass

    # erase the old tracker
    sql_query = f"DELETE FROM trackers WHERE fh_ticker IN ('{fx.fh_ticker}')"
    conn = db_connect.raw_connection()
    cursor = conn.cursor()
    cursor.execute(sql_query)
    conn.commit()
    cursor.close()

    # upload new tracker - pandas method
    try:
        fx.df_tracker.to_sql('trackers', con=db_connect, index=False, if_exists='append', method='multi')
    except IntegrityError:
        pass

    print(round((time() - start)), 'seconds to upload')
