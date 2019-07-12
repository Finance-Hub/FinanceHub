"""
Author: Gustavo Soares
"""

import pandas as pd
from bloomberg import BBG
from datetime import timedelta
from pandas.tseries.offsets import BDay
import numpy as np

class FXForwardTrackers(object):

    """
    Class for creating excess return indices for currencies using data from bloomberg.
    At the start date, we assume we trade 100 units of the base currency in 1M forward contracts
    We mart-to-market the position over the month and then roll it into the new 1M forward at the end of the month
    """

    def __init__(self, ccy_symbol, start_date='1999-12-31',end_date='today'):
        """
        Returns an object with the following attributes:
            - tickers: list with 2 strs with Bloomberg ticker for the spot rates and 1M forward rates
            - spot_rate: Series with the spot rate data
            - fwd: Series with the 1M fwd rate data
            - er_index: Series with the excess return index
            - ts_df: DataFrame with columns 'Spot', 'Fwd', and 'Excess Return Index'
        :param bbg_ticker: str, Currency symbol from Bloomberg
        :param start_date: str, when the tracker should start
        :param end_date: str, when the tracker should end
        """

        # Basic info
        currencies = [
            'AUD',
            'BRL',
            'CAD',
            'CHF',
            'CLP',
            'CZK',
            'EUR',
            'GBP',
            'HUF',
            'JPY',
            'KRW',
            'MXN',
            'NOK',
            'NZD',
            'PHP',
            'PLN',
            'SEK',
            'SGD',
            'TRY',
            'TWD',
            'ZAR',
        ]
        # TODO add ['DKK', 'ISK', 'SKK', 'HKD', 'CNY', 'MYR', 'THB', 'ARS', 'COP', 'PEN'] to the list of currencies

        if ccy_symbol not in currencies:
            print('%s not in list of currencies' % ccy_symbol)
        else:
            point_divisor_dict = {
                'AUD': 10000,
                'BRL': 10000,
                'CAD': 10000,
                'CHF': 10000,
                'CLP': 1,
                'CZK': 1000,
                'EUR': 10000,
                'GBP': 10000,
                'HUF': 100,
                'JPY': 100,
                'KRW': 1,
                'MXN': 10000,
                'NOK': 10000,
                'NZD': 10000,
                'PHP': 1,
                'PLN': 10000,
                'SEK': 10000,
                'SGD': 10000,
                'TRY': 10000,
                'TWD': 1,
                'ZAR': 10000,
            }

            bbg = BBG()
            self.ccy_symbol = ccy_symbol
            self.start_date = pd.to_datetime(start_date).date()
            self.end_date = pd.to_datetime(end_date).date()
            self.spot_rate_bbg_data = self._get_spot_rate(bbg)
            bbg_raw_fwd_data = self._get_1M_fwd_rate(bbg)

            # calculate forward outrights
            fwd_outrights = self.spot_rate_bbg_data + bbg_raw_fwd_data / point_divisor_dict[self.ccy_symbol]
            self.fwd_rate_bbg_data = fwd_outrights.fillna(method='ffill')

            quoted_as_XXXUSD = ['BRL', 'CAD', 'CHF', 'CLP', 'CZK', 'HUF',
                                'JPY', 'KRW', 'MXN', 'NOK', 'PHP', 'PLN',
                                'SGD', 'TRY', 'TWD', 'ZAR', 'SEK']

            # get all quotes vs. the USD
            if self.ccy_symbol in quoted_as_XXXUSD:
                bbg_raw_spot_data = 1/self.spot_rate_bbg_data.copy()
                fwd_outrights = 1/self.fwd_rate_bbg_data.copy()
            else:
                bbg_raw_spot_data = self.spot_rate_bbg_data.copy()
                fwd_outrights = self.fwd_rate_bbg_data.copy()

            self.ts_df = self.calculate_er_index(bbg_raw_spot_data,fwd_outrights)

    def calculate_er_index(self,spot_rate,fwd_rate):
        ts_df = pd.concat([spot_rate,fwd_rate],join='outer',axis=1,sort=True).fillna(method='ffill').dropna()
        ts_df.columns = ['spot','fwd_1m']
        er_index = pd.Series(index=ts_df.index)
        fwd_mtm = pd.Series(index=ts_df.index)
        st_dt = ts_df.index[0]
        er_index.iloc[0] = 100.
        strike = ts_df['fwd_1m'].iloc[0]
        holdings = 100. / strike
        settlement_date = st_dt + timedelta(days=30) + BDay(2)
        last_rebalance = st_dt
        # TODO: check if we need to use proper calendar functions for settlement_date calculation

        for d in ts_df.index[1:]:
            day_count = (settlement_date - d).days

            #TODO: check if we need to use proper calendar functions for day_count calculation
            spot_d = ts_df.loc[d,'spot']
            fwd_d = ts_df.loc[d, 'fwd_1m']

            # Using DC 30/365 convention for mtm of the foward
            fwd_mtm[d] = np.interp(float(day_count), [2, 32], [spot_d, fwd_d])
            er_index[d] = er_index[last_rebalance] + holdings * (fwd_mtm[d] - strike)
            if d >= settlement_date:
                strike = ts_df.loc[d,'fwd_1m']
                holdings = er_index[d] / strike
                settlement_date = d + timedelta(days=30) + BDay(2)
                last_rebalance = d

        ts_df = pd.concat([ts_df,fwd_mtm.to_frame('fwd_mtm'),er_index.to_frame('er_index')],
                          join='outer',axis=1,sort=True)
        return ts_df

    def _get_spot_rate(self,bbg):
        spot_rate_bbg_ticker = self.ccy_symbol + ' Curncy'
        bbg_raw_spot_data = bbg.fetch_series(securities=spot_rate_bbg_ticker,
                                             fields='PX_LAST',
                                             startdate=self.start_date,
                                             enddate=self.end_date)
        bbg_raw_spot_data.columns = [self.ccy_symbol]
        bbg_raw_spot_data.index = pd.to_datetime(bbg_raw_spot_data.index)
        bbg_raw_spot_data = bbg_raw_spot_data.fillna(method='ffill').dropna()
        return bbg_raw_spot_data

    def _get_1M_fwd_rate(self,bbg):
        #NDF tickers are different
        if self.ccy_symbol == 'BRL': #TODO: replace these ifs with dictionary
            fwd_rate_bbg_ticker = 'BCN1M Curncy'
        elif self.ccy_symbol == 'CLP':
            fwd_rate_bbg_ticker = 'CHN1M Curncy'
        elif self.ccy_symbol == 'TWD':
            fwd_rate_bbg_ticker = 'NTN1M BGN Curncy'
        else:
            fwd_rate_bbg_ticker = self.ccy_symbol + '1M Curncy'

        bbg_raw_fwd_data = bbg.fetch_series(securities=fwd_rate_bbg_ticker,
                                             fields='PX_LAST',
                                             startdate=self.start_date,
                                             enddate=self.end_date)
        bbg_raw_fwd_data.index = pd.to_datetime(bbg_raw_fwd_data.index)
        bbg_raw_fwd_data.columns = [self.ccy_symbol]
        bbg_raw_fwd_data = bbg_raw_fwd_data.fillna(method='ffill').dropna()
        return bbg_raw_fwd_data






