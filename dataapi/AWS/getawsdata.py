import pandas as pd


class TrackerFeeder(object):
    """
    Feeder for the trackers of the FinanceHub database.
    """

    def __init__(self, db_connect):
        """
        Feeder construction
        :param db_connect: sql connection engine from sqlalchemy
        """
        self.conn = db_connect

    def fetch(self, fh_ticker):
        """
        grabs trackers from the FH database
        :param fh_ticker: str or list with the tickers from the database trackers
        :return: pandas DataFrame with tickers on the columns
        """

        assert type(fh_ticker) is str or type(fh_ticker) is list or type(fh_ticker) is dict, \
            "'tickers' must be a string, list or dict"

        sql_query = 'SELECT time_stamp, fh_ticker, value FROM "trackers" WHERE '

        if type(fh_ticker) is str:
            sql_query = sql_query + "fh_ticker IN ('" + fh_ticker + "')"

        elif type(fh_ticker) is list:
            sql_query = sql_query + "fh_ticker IN ('" + "', '".join(fh_ticker) + "')"

        elif type(fh_ticker) is dict:
            sql_query = sql_query + "fh_ticker IN ('" + "', '".join(list(fh_ticker.keys())) + "')"

        df = pd.read_sql(sql=sql_query, con=self.conn)
        df = df.pivot(index='time_stamp', columns='fh_ticker', values='value')

        if type(fh_ticker) is dict:
            df = df.rename(fh_ticker, axis=1)

        df.index = pd.to_datetime(df.index)
        df = df.dropna(how='all')
        df = df.sort_index()

        return df

    def fetch_metadata(self):
        """
        Returns the full metadata table of the FH trackers, which is useful to do custom filters and look at what
        is in the database.
        :return: pandas Dataframe
        """
        sql_query = 'SELECT * FROM "trackers_description"'
        df = pd.read_sql(sql=sql_query, con=self.conn)
        return df

    def filter_fetch(self, filter_dict, ret='series'):
        """
        Grabs the trackers from the FH database that satisfy the criteria given by 'filter_dict'.
        :param filter_dict: dict. Keys must be column names from the metadata table. Values must be
                            either str or list of str
        :param ret: If 'series', returns the a dataframe with the tracker series that staistfy the conditions.
                    If 'tickers', returns a list of the tickers that staistfy the conditions.
        :return: list or pandas DataFrame
        """

        assert type(filter_dict) is dict, "'filter_dict' must be a dict"
        assert len(filter_dict) > 0, "'filter_dict' is empty"
        assert ret.lower() in ['series', 'tickers'], "'ret' must be either 'series' or 'ticker'"

        desc_query = 'SELECT fh_ticker FROM trackers_description WHERE '

        for col in filter_dict.keys():

            if type(filter_dict[col]) is list:
                desc_query = desc_query + col + " IN ('" + "', '".join(filter_dict[col]) + "')"
            else:
                desc_query = desc_query + col + f" IN ('{filter_dict[col]}')"

            desc_query = desc_query + ' and '

        desc_query = desc_query[:-5]
        df = pd.read_sql(sql=desc_query, con=self.conn)

        tickers = df.values.flatten().tolist()

        if ret == 'tickers':
            return tickers

        df = self.fetch(tickers)
        return df

    def filter_parameters(self):
        """
        Grabs the possible columns and their respective unique values from the metadata table.
        :return: dict. Keys are the column names, values are list of unique values of the column.
        """

        df = self.fetch_metadata()

        param_dict = {}

        for col in df.columns:
            param_dict[col] = df[col].unique().tolist()

        return param_dict

    def fetch_everything(self):
        sql_query = 'SELECT time_stamp, fh_ticker, value FROM "trackers"'

        df = pd.read_sql(sql=sql_query, con=self.conn)
        df = df.pivot(index='time_stamp', columns='fh_ticker', values='value')

        df.index = pd.to_datetime(df.index)
        df = df.dropna(how='all')
        df = df.sort_index()

        return df
