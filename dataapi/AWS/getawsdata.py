"""
Author: Gustavo Amarante
"""

import numpy as np
import pandas as pd
from datetime import datetime


class TrackerFeeder(object):
    """
    Feeder for the trackers of the FinanceHub database.
    """

    def __init__(self, db_connect):
        """
        Feeder construction
        :param db_connect: sql connection engine from sqlalchemy
        """
        self.conn = db_connect.connection

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


class FocusFeeder(object):

    def __init__(self, db_connect):
        """
        Feeder construction
        :param db_connect: sql connection engine from sqlalchemy
        """
        self.conn = db_connect.connection

    def fetch(self, index='ipca', frequency='yearly', prediction_scope=None,
              dt_ini=None, dt_end=None):

        """
        Grabs data from the data base and pivots the results into a dataframe. To assure consistency The function can
        only take one index at a time and one frequency at a time. Only'prediction_scope' can be a list.
        If no prediction scope is passed, all available prediction scopes are returned.
        :param index: String containing the name of the index.
        :param frequency: String. 'yearly', 'monthly' or 'quarterly' (availability depends on the index)
        :param prediction_scope: string, float or list. Years that the forecasts are for.
        :param dt_ini: string. Initial date for the series
        :param dt_end: string. End date for the series
        :return: pandas DataFrame with the pivoted data.
        """

        # Error Checking
        self._basic_assertions(index, frequency, prediction_scope)

        # Handle formats
        index, frequency, prediction_scope, dt_ini, dt_end, pivot \
            = self._map_inputs(index, frequency, prediction_scope, dt_ini, dt_end)

        # build sql query
        sql_query = self._build_sql_query(index, frequency, prediction_scope, dt_ini, dt_end)

        # get data
        df = pd.read_sql(sql=sql_query, con=self.conn)
        df = df.drop_duplicates()

        # pivoting
        df = df.pivot(index='date', columns=pivot, values='value')
        df.index = pd.to_datetime(df.index)

        return df

    def years_ahead(self, index='IPCA', years=1, dt_ini=None, dt_end=None):
        """
        The metric atribute is set to 'mean' by default because further projections change smoothly
        """

        # Error checking
        self._basic_assertions_years_ahead(index, years)

        # Handle formats
        index, dt_ini, dt_end = self._map_inputs_years_ahead(index, dt_ini, dt_end)

        # grabs the index for all available years for each date
        df = self.fetch(index=index, frequency='yearly', prediction_scope=None,
                        dt_ini=dt_ini, dt_end=dt_end)

        # creates the new dataframe
        df_weighted = pd.DataFrame(index=df.index)
        df_weighted[index + ' ' + str(years) + ' year ahead'] = np.nan

        # days until year end
        df_weighted['D2YE'] = ((df_weighted.index + pd.offsets.YearEnd()) -
                               pd.to_datetime(df_weighted.index.tolist())).days

        for ind in df_weighted.index:
            if ind.day == 31 and ind.month == 12:
                df_weighted.loc[ind, 'D2YE'] = 0

        # loops on each date
        for date in df_weighted.index:
            df_weighted.loc[date, index + ' ' + str(years) + ' year ahead'] = \
                (df.loc[date, str(date.year + years - 1)] * df_weighted.loc[date, 'D2YE'] +
                 df.loc[date, str(date.year + years)] * (365 - df_weighted.loc[date, 'D2YE'])) / 365

        df = df_weighted[[index + ' ' + str(years) + ' year ahead']].interpolate()
        df.index = pd.to_datetime(df.index)

        return df

    @staticmethod
    def _basic_assertions(index, frequency, prediction_scope):
        """Check basic assertions"""

        assert type(index) is str, 'index must be a string'

        assert type(frequency) is str, 'frequency must be a string'

    @staticmethod
    def _map_inputs(index, frequency, prediction_scope, dt_ini, dt_end):
        """Handle formats of the inputs"""

        # index
        if type(index) is str:
            index = index.lower()
        elif type(index) is list:
            index = [x.lower() for x in index]

        # frequency
        frequency = frequency.lower()

        # prediction_scope
        if type(prediction_scope) is str:
            prediction_scope = prediction_scope.lower()
        elif type(prediction_scope) is list:
            prediction_scope = [str(x).lower() for x in prediction_scope]
        elif prediction_scope is None:
            prediction_scope = None
        else:
            prediction_scope = str(prediction_scope).lower()

        # dates
        if dt_ini is None:
            dt_ini = '1900-01-01'

        if dt_end is None:
            dt_end = datetime.now().strftime('%Y-%m-%d')

        # pivot variable (while we have no metrics, its always the prediction scope)
        pivot = 'prediction_scope'

        return index, frequency, prediction_scope, dt_ini, dt_end, pivot

    @staticmethod
    def _build_sql_query(index, frequency, prediction_scope, dt_ini, dt_end):

        sql_query = 'SELECT DATE, VALUE, PREDICTION_SCOPE FROM "focus_survey" WHERE '

        # index (must not be None)
        if type(index) is str:
            sql_query = sql_query + "lower(INDEX) IN ('" + index + "')"
        elif type(index) is list:
            sql_query = sql_query + "lower(INDEX) IN ('" + "', '".join(index) + "')"

        # frequency
        if type(frequency) is str:
            sql_query = sql_query + " AND lower(FREQUENCY) IN ('" + frequency + "')"
        elif type(frequency) is list:
            sql_query = sql_query + " AND lower(FREQUENCY) IN ('" + "', '".join(frequency) + "')"

        # prediction scope
        if type(prediction_scope) is str:
            sql_query = sql_query + " AND lower(PREDICTION_SCOPE) IN ('" + prediction_scope + "')"
        elif type(prediction_scope) is list:
            sql_query = sql_query + " AND lower(PREDICTION_SCOPE) IN ('" + "', '".join(prediction_scope) + "')"

        sql_query = sql_query + " AND DATE BETWEEN '" + dt_ini + "' AND '" + dt_end + "'"

        sql_query = sql_query + ' ORDER BY DATE;'

        return sql_query

    @staticmethod
    def _basic_assertions_years_ahead(index, years):
        """Check basic assertions"""

        assert type(index) is str, 'index must be a string'

        assert (type(years) is int) and (years <= 4), 'number of years must be an intger between 1 and 4'

    @staticmethod
    def _map_inputs_years_ahead(index, dt_ini, dt_end):
        """Handles the format of the inputs of the years_ahead method"""

        index = index.lower()

        # dates
        if dt_ini is None:
            dt_ini = '1900-01-01'

        if dt_end is None:
            dt_end = datetime.now().strftime('%Y-%m-%d')

        return index, dt_ini, dt_end

