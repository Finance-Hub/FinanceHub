import pandas as pd


class TrackerFeeder(object):
    # TODO usuario pode passar db_connect ou connect dict

    def __init__(self, db_connect):
        self.conn = db_connect

    def fetch(self, fh_ticker):

        assert type(fh_ticker) is str or type(fh_ticker) is list or type(fh_ticker) is dict, \
            "'tickers' must be a string, list or dict"

        sql_query = 'SELECT time_stamp, fh_ticker, value FROM "trackers" WHERE '

        if type(fh_ticker) is str:
            sql_query = sql_query + "fh_ticker IN ('" + fh_ticker + "')"

        elif type(fh_ticker) is list:
            sql_query = sql_query + "fh_ticker IN ('" + "', '".join(fh_ticker) + "')"

        elif type(fh_ticker) is dict:
            sql_query = sql_query + "fh_ticker IN ('" + "', '".join(list(fh_ticker.keys())) + "')"

        # TODO filter asset_class, type, exchange_symbol, currency, country, sector, group

        df = pd.read_sql(sql=sql_query, con=self.conn)
        df = df.pivot(index='time_stamp', columns='fh_ticker', values='value')

        if type(fh_ticker) is dict:
            df = df.rename(fh_ticker, axis=1)

        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        return df

    def fetch_metadata(self):
        sql_query = 'SELECT * FROM "trackers_description"'
        df = pd.read_sql(sql=sql_query, con=self.conn)
        return df
