import pandas as pd


class SGS(object):
    """
    Wrapper for the Data API of the SGS (Sistema de Gerenciamento de Séries) of the Brazilian Central Bank.
    """

    def fetch(self, series_id, initial_date=None, end_date=None):
        """
        Grabs series from the SGS

        :param series_id: series code on the SGS. (int, str, list of int or list of str)
        :param initial_date: initial date for the result (optional)
        :param end_date: end date for the result (optional)
        :return: pandas DataFrame withe the requested series. If a dict is passed as series ID, the dict values are used
                 as column names.
        """

        if type(series_id) is list:  # loop all series codes

            df = pd.DataFrame()

            for cod in series_id:
                single_series = self._fetch_single_code(cod, initial_date, end_date)
                df = pd.concat([df, single_series], axis=1)

            df.sort_index(inplace=True)

        elif type(series_id) is dict:

            df = pd.DataFrame()

            for cod in series_id.keys():
                single_series = self._fetch_single_code(cod, initial_date, end_date)
                df = pd.concat([df, single_series], axis=1)

            df.columns = series_id.values()

        else:
            df = self._fetch_single_code(series_id, initial_date, end_date)

        df = self._correct_dates(df, initial_date, end_date)

        return df

    def _fetch_single_code(self, series_id, initial_date=None, end_date=None):
        """
        Grabs a single series using the API of the SGS. Queries are built using the url
        http://api.bcb.gov.br/dados/serie/bcdata.sgs.{seriesID}/dados?formato=json&dataInicial={initial_date}&dataFinal={end_date}

        The url returns a json file which is read and parsed to a pandas DataFrame.

        ISSUE: It seems like the SGS API URL is not working properly. Even if you pass and initial or end date argument,
        the API does not filter the dates and always returns all the available values. I added a date filter for the
        pandas dataframe that is passed to the user and left the old code intact, in case this gets corrected in the
        future.

        :param series_id: series code on the SGS
        :param initial_date: initial date for the result (optional)
        :param end_date: end date for the result (optional)
        :return: pandas DataFrame with a single series as column and the dates as the index
        """

        url = self._build_url(series_id, initial_date, end_date)

        df = pd.read_json(url)
        df = df.set_index(pd.to_datetime(df['data'], dayfirst=True)).drop('data', axis=1)
        df.columns = [str(series_id)]

        return df

    @staticmethod
    def _build_url(series_id, initial_date, end_date):
        """ returns the search url as string """

        url = 'http://api.bcb.gov.br/dados/serie/bcdata.sgs.' + str(series_id) + '/dados?formato=json'

        if not (initial_date is None):
            url = url + '&dataInicial=' + str(initial_date)

        if not (end_date is None):
            url = url + '&dataFinal=' + str(end_date)

        return url

    @staticmethod
    def _correct_dates(df, initial_date, end_date):

        if initial_date is not None:
            dt_ini = pd.to_datetime(initial_date, dayfirst=True)
            df = df[df.index >= dt_ini]

        if end_date is not None:
            dt_end = pd.to_datetime(end_date, dayfirst=True)
            df = df[df.index <= dt_end]

        return df
