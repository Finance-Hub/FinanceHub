import os
import wget
import datetime as dt
import pandas as pd
from dateutil.relativedelta import relativedelta

class BrazilianBonds(object):
    
    def scrape(self, initial_month, end_month, initial_year, end_year, n = "E"):
        """
        Information is available at:
        http://www4.bcb.gov.br/pom/demab/negociacoes/apresentacao.asp?idpai=SELICOPERACAO
                
        Gets a single series from BACEN. Data is fetched using the url:
        http://www4.bcb.gov.br/pom/demab/negociacoes/download/NegNaaaamm.ZIP
        N should be eighter T(All trades) or E(excludes intracompanies trades)
        aaaamm is the year and month of the trades
          
        The url stores a zip file with a single .csv for each date so code runs a loop
        to fecth data from each year within the time interval specified and save it to a pandas DataFrame
        
        :param initial_year: First year of the query.
        :param end_year: Last year of the query.
        :param initial_month: Optional, firt month of the first year.
        :param end_month: Optional, last month of the last year.
        :param n: T or E, includes or excludes Intracompanies trades.
        :return: pandas DataFrame with the requested series.     
        """
        
        lista = self._get_dates(initial_year, end_year, initial_month, end_month)
        
        titulos_publicos = []
    
        for date in lista :
      
            file = 'Neg' + n + date + '.zip'
            url  = 'http://www4.bcb.gov.br/pom/demab/negociacoes/download/' + file

            print(url)

            wget.download(url)
    
            titulos_publicos.append(pd.read_csv(file, sep = ";"))

            os.remove(file)
  
        titulos_publicos = pd.concat(titulos_publicos)
        
        return titulos_publicos
    
    @staticmethod
    def _get_dates(initial_year = None, end_year = None, initial_month = None, end_month = None):
        """    
        :param initial_year: initial year for the time interval. If None, uses the first available date at BACEN.
        :param end_year: end year for the time interval. If None, use today.
        :param initial_month: initial month. If None, uses the first available date at BACEN.
        :param end_month: end month for the time interval. If None or if only year specified, use today.
        :return: pandas DataFrame with the time interval specified.
        """
        
        oldest_year = "2003"
        oldest_month = "1"
        
        if initial_year is None or initial_year < oldest_year:
            initial_year = oldest_year
        
        if end_year  is None or end_year > dt.date.today().strftime('%Y'):
            end_year = dt.date.today().strftime('%Y')
            
        if initial_month is None:
            initial_month = oldest_month

        if end_month  is None or end_month.zfill(2) > dt.date.today().strftime('%m'):
            end_month = dt.date.today().strftime('%m')       
            
        star_date = format(int(initial_year), '04d' ) + format(int(initial_month), '02d')
        end_date = format(int(end_year), '04d' ) + format(int(end_month), '02d')

        fmt = '%Y%m'
        start_date = dt.datetime.strptime(star_date, fmt).date()
        end_date = dt.datetime.strptime(end_date, fmt).date()

        d = start_date
        step = relativedelta(months=+1)

        lista = list()

        while d <= end_date:
            lista += [d.strftime('%Y%m')]
            d += step  
            
        return lista
                        
