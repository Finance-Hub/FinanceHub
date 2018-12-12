"""
Author: Vitor Eller
"""

import pandas as pd
from datetime import datetime, timedelta
from time import strptime


class CETIP(object):
    
    def fetch(self, series_id, initial_date=None, end_date=None):
        """
        Grabs series from CETIP
        
        :param series_id: series code on CETIP. (str or list of str: {'MediaCDI', 'VolumeCDI', 'IndiceDI'})
        :param initial_date: initial date for the result. (optional)
        :param end_date: end date for the result. (optional)
        :return: pandas DataFrame with the requested series.
        """
        
        if type(series_id) is list:
            
            df = pd.DataFrame()
            
            for cod in series_id:
                series = self._fetch_single_series(cod, initial_date, end_date)
                df = pd.concat([df, series], axis=1)
        
            df.sort_index(inplace=True)
        
        else:
            
            df = self._fetch_single_series(series_id, initial_date, end_date)
        
        return df
    
    def _fetch_single_series(self, series_id, initial_date, end_date):
        """
        Gets a single series from CETIP through its FTP. Data is fetched using the url 
        ftp://ftp.cetip.com.br/{series_id}
        
        The url stores a collection with specific .txt files for each date so code runs a loop
        to fecth data from each day within the time interval specified and save it to a pandas DataFrame
        
        :param series_id: series code on CETIP. (str or list of str)
        :param initial_date: initial date for the result. (optional)
        :param end_date: end date for the result. (optional)
        :return: pandas DataFrame with the requested series.     
        """
        
        dates = self._get_dates(initial_date, end_date)
        df = pd.DataFrame()
        
        for date in dates:
            
            url = f'ftp://ftp.cetip.com.br/{series_id}/{date.strftime("%Y%m%d")}.txt'
            try:
                
                data = pd.read_csv(url, header=None).iloc[0, 0]
                
                if series_id == 'MediaCDI':
                    # CDI needs to be converted to percentage
                    data = data/100
                    
                df.loc[date, series_id] = data
            
            except:
                # expected behaviour is skipping holidays and weekends
                continue
        
        return df
    
    @staticmethod
    def _get_dates(initial_date, end_date):
        """
        :param initial_date: initial date for the time interval. If None, uses the first available date on CETIP
        :param end_date: end date for the time interval. If None, uses the previous day.
        :return: pandas DataFrame with the time interval specified.
        """
        
        oldest_date = "2012-08-20"
        
        if initial_date is None or (strptime(initial_date, '%Y-%m-%d') < strptime(initial_date, '%Y-%m-%d')):
            initial_date = oldest_date
        
        if end_date is None:
            end_date = (datetime.today() - timedelta(1)).strftime('%Y-%m-%d')
            
        df = pd.date_range(initial_date, end_date, freq='D')
        
        return df
    
"""
To Do:
* Code runs slow since it needs to read one .txt for each day. Think of a strategy to accelerate this process.
"""