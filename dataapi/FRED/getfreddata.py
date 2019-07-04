"""
Author: Gustavo Amarante
"""

import pandas as pd


class FRED(object):
    """
    Wrapper for the data API of the FRED
    """

    def fetch(self, series_id, initial_date=None, end_date=None):
        """
        Grabs series from the FRED website and returns a pandas dataframe

        :param series_id: string with series ID, list of strings of the series ID or dict with series ID as keys
        :param initial_date: string in the format 'yyyy-mm-dd' (optional)
        :param end_date: string in the format 'yyyy-mm-dd' (optional)
        :return: pandas DataFrame withe the requested series. If a dict is passed as series ID, the dict values are used
                 as column names.
        """

        if type(series_id) is list:

            df = pd.DataFrame()

            for cod in series_id:
                single_series = self._fetch_single_code(cod)
                df = pd.concat([df, single_series], axis=1)

            df.sort_index(inplace=True)

        elif type(series_id) is dict:

            df = pd.DataFrame()

            for cod in series_id.keys():
                single_series = self._fetch_single_code(cod)
                df = pd.concat([df, single_series], axis=1)

            df.columns = series_id.values()

        else:

            df = self._fetch_single_code(series_id)

        df = self._correct_dates(df, initial_date, end_date)

        return df

    @staticmethod
    def _fetch_single_code(series_id):

        url = r'https://fred.stlouisfed.org/data/' + series_id + '.txt'
        df = pd.read_csv(url, sep='\n')
        series_start = df[df[df.columns[0]].str.contains('DATE\s+VALUE')].index[0] + 1
        df = df.loc[series_start:]
        df = df[df.columns[0]].str.split('\s+', expand=True)
        df = pd.DataFrame(data=df[1].values.astype(float), index=pd.to_datetime(df[0]), columns=[series_id])
        df.index.rename('Date', inplace=True)

        return df

    @staticmethod
    def _correct_dates(df, initial_date, end_date):

        if initial_date is not None:
            dt_ini = pd.to_datetime(initial_date)
            df = df[df.index >= dt_ini]

        if end_date is not None:
            dt_end = pd.to_datetime(end_date)
            df = df[df.index <= dt_end]

        return df
