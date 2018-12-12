"""
Author: Vitor Eller - @VFermat
"""

import pandas as pd
from pandas.tseries.offsets import MonthEnd


class HXLFactor(object):
    
    def calculate_factors(self, prices, dividends, assets, roe, marketcap):
        
        # Lining up dates to end of month
        prices.columns = prices.columns + MonthEnd(0)
        dividends.columns = dividends.columns + MonthEnd(0)
        assets.columns = assets.columns + MonthEnd(0)
        roe.columns = roe.columns + MonthEnd(0)
        marketcap.columns = marketcap.columns + MonthEnd(0)

        dividends, assets, roe = self._padronize_columns(prices.columns,
                                                         dividends,
                                                         assets,
                                                         roe)
        
        self.securities = {
                'assets': assets,
                'ROE': roe,
                'price': prices,
                'marketcap': marketcap,
                'dividends': dividends
                }
        
        # Gathering info
        self.securities = self._get_IA_info(self.securities)
        self.securities = self._get_return(self.securities)
        self.securities = self._get_benchmarks(self.securities)

    @staticmethod
    def _get_benchmarks(securities):
        pass
    
    @staticmethod
    def _get_return(securities):
        """
        Calculates the return for each security over time and related information.
    
        Parameters
        ----------
        securities : Dict like
            A dictionary containing the information on stocks. 
            
        Return
        ----------
        n_securities : Dict
            Updated dict containing the return for each security over time.
        """
        
        n_securities = securities.copy()
        
        n_securities['lprice'] = n_securities['price'].shift(1, axis=1)
        n_securities['pdifference'] = n_securities['price'] - n_securities['lprice']
        n_securities['gain'] = n_securities['dividends'] + n_securities['pdifference']
        n_securities['return'] = n_securities['gain']/n_securities['lprice']
        
        # Creates a return field which is shifted one month back. Will be used 
        # when calculating the factors
        n_securities['lreturn'] = n_securities['return'].shift(-1, axis=1)
        
        return n_securities

    @staticmethod
    def _get_IA_info(securities):
        """
        Calculates the Investment over Assets ratio and related information
    
        Parameters
        ----------
        securities : Dict like
            A dict containing the information on stocks. 
            
        Return
        ----------
        n_securities : Dict
            Updated dict containing Investment over Assets ratio and related information.
        """
        
        n_securities = securities.copy()
        # Calculates 1-year-lagged-assets
        n_securities['lassets'] = n_securities['assets'].shift(12, axis=1)
        # Calculates Investment
        n_securities['investment'] = n_securities['assets'] - n_securities['lassets']
        # Calculates Investment over Assets ratio
        n_securities['I/A'] = n_securities['investment']/n_securities['lassets']
        
        return n_securities
    
    @staticmethod
    def _padronize_columns(pattern, dividends, assets, ROE):
        """
        Padronizes information that is not released monthly. In that way, we do not
        encounter problems while manipulating data.
        
        Parameters
        ----------
        pattern : Array like
            Array containing the pattern for the columns
        dividends : DataFrame like
            Dataframe containing information on dividends
        assets : DataFrame like
            Dataframe containing information on assets
        ROE : DataFrame like
            Dataframe containing information on ROE

        Return
        ----------
        ndividends : Dataframe like
            Updated Dataframe containing information on dividends
        nassets : Dataframe like
            Updated Dataframe containing information on assets
        n_roe : Dataframe like
            Updated Dataframe containing information on ROE
        """
        
        ndividends = pd.DataFrame(index=dividends.index)
        nassets = pd.DataFrame(index=assets.index)
        n_roe = pd.DataFrame(index=ROE.index)
        
        for date in pattern:
            
            if date in dividends.columns:
                ndividends[date] = dividends[date]
            else:
                ndividends[date] = 0
                
            if date in assets.columns:
                nassets[date] = assets[date]
                n_roe[date] = ROE[date]
            else:
                nassets[date] = 0
                n_roe[date] = 0
            
        return ndividends, nassets, n_roe


"""
TO DO:
    Maneira para que todos os index sejam o ultimo dia do mes.
    Arrumar um jeito de fazer groupby com panels.
"""