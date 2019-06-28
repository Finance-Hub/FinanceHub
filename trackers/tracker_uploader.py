from trackers import SingleNameEquity
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

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

# ===== EQUITY SINGLE NAMES =====
stocks = ['PETR4 BZ Equity']

for s in stocks:
    sne = SingleNameEquity(s)

    # uploads the metadata
    print(s, 'uploading metadata')
    try:
        sne.df_metadata.to_sql('trackers_description', con=db_connect, index=False, if_exists='append')
    except IntegrityError:
        pass

    # erase the old tracker
    print(s, 'erase old tracker')
    sql_query = f"DELETE FROM trackers WHERE fh_ticker IN ('{sne.fh_ticker}')"
    conn = db_connect.raw_connection()
    cursor = conn.cursor()
    cursor.execute(sql_query)
    conn.commit()
    cursor.close()

    # upload new tracker
    print(s, 'uploading new tracker')
    try:
        sne.df_tracker.to_sql('trackers', con=db_connect, index=False, if_exists='append')
    except IntegrityError:
        pass

