"""
Author: Gustavo Amarante
"""

import requests
import pandas as pd


class IMF(object):
    """
    Wrapper around the IMF data API
    http://datahelp.imf.org/knowledgebase/articles/667681-json-restful-web-service
    """

    @staticmethod
    def dataflow():
        """
        Returns a pandas DataFrame where the first column 'Database ID' is the database ID for further usage.
        The second column 'Database Name' is the description of each database.
        """

        url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow'
        raw_request = requests.get(url)
        df_request = pd.DataFrame(raw_request.json()['Structure']['Dataflows']['Dataflow'])

        ids = df_request['KeyFamilyRef'].apply(lambda x: x['KeyFamilyID'])
        names = df_request['Name'].apply(lambda x: x['#text'])

        return pd.DataFrame({'Database ID': ids, 'Database Name': names})

    def data_structure(self, database_id, check_query=True):
        """
        This method helps to build the query of a given IMF dataset
        :param database_id: name of the table with the data from the IMF
        :param check_query: check if the selected table is available
        :return: a tuple where the first entry is a list with the query parameters and the second entry  is a dictionary
                 where the keys are the query parameters and the values are pandas DataFrames with the possible values
                 for that query
        """

        if check_query:
            available_datasets = self.dataflow()['Database ID'].tolist()

            if database_id not in available_datasets:
                print('Database not available')
                return None, None

        url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/DataStructure/' + database_id
        raw_request = requests.get(url)

        if not raw_request.ok:
            print('Request returned nothing')
            return None, None

        rparsed = raw_request.json()['Structure']
        dim_code = pd.Series(rparsed['KeyFamilies']['KeyFamily']['Components']['Dimension']).apply(
            lambda x: x['@codelist']).tolist()
        dim_codedict = [x for x in rparsed['CodeLists']['CodeList'] if x['@id'] in dim_code]
        dim_codedict = dict(zip(pd.Series(dim_codedict).apply(lambda x: x['@id']).tolist(), dim_codedict))

        for k in dim_codedict.keys():
            dim_codedict[k] = pd.DataFrame({'CodeValue': pd.Series(dim_codedict[k]['Code'])
                                           .apply(lambda x: x['@value']), 'CodeText': pd.Series(dim_codedict[k]['Code'])
                                           .apply(lambda x: x['Description']['#text'])})

        return dim_code, dim_codedict

    def compact_data(self, database_id, queryfilter, series_name, startdate=None, enddate=None,
                     checkquery=False, verbose=False):
        """
        Grabs the data from the IMF
        :param database_id: dataset name
        :param queryfilter: dict with the query parameters as keys and their selected dimension as values
        :param series_name: name to be used in the column of the output DataFrame
        :param startdate: Date filter (optional)
        :param enddate: Date filter (optional)
        :param checkquery: check if the dataset is available
        :param verbose: print the progress
        :return: a pandas DataFrame with the selected data
        """

        if checkquery:
            available_datasets = self.dataflow()['DatabaseID'].tolist()
            if database_id not in available_datasets:
                return None

        request_url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/' + database_id + '/'

        for k in queryfilter.keys():
            request_url = request_url + queryfilter[k] + '.'

        if not (startdate is None):
            request_url = request_url + '?startPeriod=' + startdate

        if not (enddate is None):
            request_url = request_url + '?endPeriod=' + enddate

        raw_request = requests.get(request_url)

        if verbose:
            print('\nmaking API call:\n')
            print(request_url)
            print('\n')

        if not raw_request.ok:
            print('Bad request')
            return None

        rparsed = raw_request.json()

        if 'Series' not in list(rparsed['CompactData']['DataSet'].keys()):
            print('no data available \n')
            return None

        return_df = pd.DataFrame(rparsed['CompactData']['DataSet']['Series']['Obs']).set_index('@TIME_PERIOD')
        return_df.index.rename(None, inplace=True)
        return_df.index = pd.to_datetime(return_df.index)
        return_df.columns = [series_name]
        return_df[series_name] = return_df[series_name].astype(float)

        return return_df
