"""
Author: Gustavo Soares
"""

import numpy as np
import pandas as pd
from bloomberg import BBG
from datetime import timedelta
from pandas.tseries.offsets import BDay

class FXForwardTrackers(object):
    """
    Class for creating excess return indices for currencies using data from bloomberg.
    At the start date, we assume we trade 100 units of the base currency in 1M forward contracts.
    We mark-to-market the position over the month and then roll it into the new 1M forward at the end of the month
    """

    # Currently available currencies
    # TODO add 'DKK', 'ISK', 'SKK', 'HKD', 'CNY', 'MYR', 'THB', 'ARS', 'COP', 'PEN' to the list of currencies
    currencies = ['AUD', 'BRL', 'CAD', 'CHF', 'CLP', 'CZK', 'EUR', 'GBP', 'HUF', 'JPY', 'KRW',
                  'MXN', 'NOK', 'NZD', 'PHP', 'PLN', 'SEK', 'SGD', 'TRY', 'TWD', 'ZAR']

    point_divisor_dict = {'AUD': 10000,
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
                          'ZAR': 10000}

    fwd_1M_dict = {'AUD': 'AUD1M Curncy',
                   'BRL': 'BCN1M Curncy',
                   'CAD': 'CAD1M Curncy',
                   'CHF': 'CHF1M Curncy',
                   'CLP': 'CHN1M Curncy',
                   'CZK': 'CZK1M Curncy',
                   'EUR': 'EUR1M Curncy',
                   'GBP': 'GBP1M Curncy',
                   'HUF': 'HUF1M Curncy',
                   'JPY': 'JPY1M Curncy',
                   'KRW': 'KRW1M Curncy',
                   'MXN': 'MXN1M Curncy',
                   'NOK': 'NOK1M Curncy',
                   'NZD': 'NZD1M Curncy',
                   'PHP': 'PHP1M Curncy',
                   'PLN': 'PLN1M Curncy',
                   'SEK': 'SEK1M Curncy',
                   'SGD': 'SGD1M Curncy',
                   'TRY': 'TRY1M Curncy',
                   'TWD': 'NTN1M BGN Curncy',
                   'ZAR': 'ZAR1M Curncy'}

    quoted_as_XXXUSD = ['BRL', 'CAD', 'CHF', 'CLP', 'CZK', 'HUF', 'JPY', 'KRW', 'MXN', 'NOK',
                        'PHP', 'PLN', 'SGD', 'TRY', 'TWD', 'ZAR', 'SEK']

    iso_country_dict = {'AUD': 'AU',
                        'BRL': 'BR',
                        'CAD': 'CA',
                        'CHF': 'CH',
                        'CLP': 'CL',
                        'CZK': 'CZ',
                        'EUR': 'EU',
                        'GBP': 'GB',
                        'HUF': 'HU',
                        'JPY': 'JP',
                        'KRW': 'KR',
                        'MXN': 'MX',
                        'NOK': 'NO',
                        'NZD': 'NZ',
                        'PHP': 'PH',
                        'PLN': 'PL',
                        'SEK': 'SE',
                        'SGD': 'SG',
                        'TRY': 'TR',
                        'TWD': 'TW',
                        'ZAR': 'ZA'}

    def __init__(self, ccy_symbol, start_date='1999-12-31', end_date='today'):
        """
        Returns an object with the following attributes:
            - tickers: list with 2 strs with Bloomberg ticker for the spot rates and 1M forward rates
            - spot_rate: Series with the spot rate data
            - fwd: Series with the 1M fwd rate data
            - er_index: Series with the excess return index
            - ts_df: DataFrame with columns 'Spot', 'Fwd', and 'Excess Return Index'
        :param ccy_symbol: str, Currency symbol from Bloomberg
        :param start_date: str, when the tracker should start
        :param end_date: str, when the tracker should end
        """

        assert ccy_symbol in self.currencies, f'{ccy_symbol} not currently supported'

        self.bbg = BBG()
        self.ccy_symbol = ccy_symbol
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.spot_rate = self._get_spot_rate()
        raw_fwd = self._get_1m_fwd_rate()
        self.country = self.iso_country_dict[self.ccy_symbol]
        self.fh_ticker = 'fx ' + self.country.lower() + ' ' + self.ccy_symbol.lower()
        self.df_metadata = self._get_metadata()

        # calculate forward outrights
        fwd_outrights = self.spot_rate + raw_fwd / self.point_divisor_dict[self.ccy_symbol]
        self.fwd_rate_bbg_data = fwd_outrights.fillna(method='ffill')

        # get all quotes vs. the USD
        if self.ccy_symbol in self.quoted_as_XXXUSD:
            bbg_raw_spot_data = 1/self.spot_rate
            fwd_outrights = 1/self.fwd_rate_bbg_data
        else:
            bbg_raw_spot_data = self.spot_rate
            fwd_outrights = self.fwd_rate_bbg_data

        self.df_tracker = self._calculate_tr_index(bbg_raw_spot_data, fwd_outrights)
        self.df_tracker = self._get_tracker_melted()

    @staticmethod
    def _calculate_tr_index(spot_rate, fwd_rate):
        ts_df = pd.concat([spot_rate, fwd_rate], axis=1, sort=True).fillna(method='ffill').dropna()
        ts_df.columns = ['spot', 'fwd_1m']
        er_index = pd.Series(index=ts_df.index)
        fwd_mtm = pd.Series(index=ts_df.index)
        st_dt = ts_df.index[0]
        er_index.iloc[0] = 100.
        strike = ts_df['fwd_1m'].iloc[0]
        holdings = 100. / strike
        # TODO: check if we need to use proper calendar for settlement_date calculation
        settlement_date = st_dt + timedelta(days=30) + BDay(2)
        last_rebalance = st_dt

        for d in ts_df.index[1:]:
            # TODO: check if we need to use proper calendar for day_count calculation
            day_count = (settlement_date - d).days

            spot_d = ts_df.loc[d, 'spot']
            fwd_d = ts_df.loc[d, 'fwd_1m']

            # Using DC 30/365 convention for mtm of the foward
            fwd_mtm[d] = np.interp(float(day_count), [2, 32], [spot_d, fwd_d])
            er_index[d] = er_index[last_rebalance] + holdings * (fwd_mtm[d] - strike)
            if d >= settlement_date:
                strike = ts_df.loc[d, 'fwd_1m']
                holdings = er_index[d] / strike
                settlement_date = d + timedelta(days=30) + BDay(2)
                last_rebalance = d

        return er_index.to_frame('er_index')

    def _get_spot_rate(self):
        spot_rate_bbg_ticker = self.ccy_symbol + ' Curncy'
        bbg_raw_spot_data = self.bbg.fetch_series(securities=spot_rate_bbg_ticker,
                                                  fields='PX_LAST',
                                                  startdate=self.start_date,
                                                  enddate=self.end_date)
        bbg_raw_spot_data.columns = [self.ccy_symbol]
        bbg_raw_spot_data = bbg_raw_spot_data.fillna(method='ffill').dropna()
        return bbg_raw_spot_data

    def _get_1m_fwd_rate(self):

        bbg_raw_fwd_data = self.bbg.fetch_series(securities=self.fwd_1M_dict[self.ccy_symbol],
                                                 fields='PX_LAST',
                                                 startdate=self.start_date,
                                                 enddate=self.end_date)
        bbg_raw_fwd_data.columns = [self.ccy_symbol]
        bbg_raw_fwd_data = bbg_raw_fwd_data.fillna(method='ffill').dropna()
        return bbg_raw_fwd_data

    def _get_metadata(self):
        df = pd.DataFrame(index=[0],
                          data={'fh_ticker': self.fh_ticker,
                                'asset_class': 'FX',
                                'type': 'currency forward',
                                'exchange_symbol': self.ccy_symbol,
                                'currency': 'USD',
                                'country': self.country,
                                'maturity': 1/12})
        return df

    def _get_tracker_melted(self):
        df = self.df_tracker[['er_index']].rename({'er_index': self.fh_ticker}, axis=1)
        df['time_stamp'] = df.index.to_series()
        df = df.melt(id_vars='time_stamp', var_name='fh_ticker', value_name='value')
        df = df.dropna()
        return df


class FXCarryTrackers(object):


    # TODO add ['CNH', 'ILS'] to the list of currencies and deposit rates
    currencies = [
        'EUR',
        'JPY',
        'GBP',
        'CHF',
        'CAD',
        'AUD',
        'NZD',
        'NOK',
        'SEK',
        'DKK',
        'CZK',
        'HUF',
        'ISK',
        'PLN',
        'SKK',
        'TRY',
        'ZAR',
        'HKD',
        'INR',
        'IDR',
        'PHP',
        'SGD',
        'KRW',
        'CNY',
        'MYR',
        'TWD',
        'THB',
        'ARS',
        'BRL',
        'CLP',
        'COP',
        'MXN',
        'PEN',
        'RUB'
    ]

    deposit_rates_dict = {
        'EUR': 'EUDRC',
        'JPY': 'JYDRC',
        'GBP': 'BPDRC',
        'CHF': 'SFDRC',
        'CAD': 'CDDRC',
        'AUD': 'ADDRC',
        'NZD': 'NDDRC',
        'NOK': 'NKDRC',
        'SEK': 'SKDRC',
        'DKK': 'DKDRC',
        'CZK': 'CKDRC',
        'HUF': 'HFDRC',
        'ISK': 'IKDRC',
        'PLN': 'PZDRC',
        'SKK': 'VKDRC',
        'TRY': 'TYDRC',
        'ZAR': 'SADRC',
        'HKD': 'HDDRC',
        'INR': 'IRDRC',
        'IDR': 'IHDRC',
        'PHP': 'PPDRC',
        'SGD': 'SDDRC',
        'KRW': 'KWDRC',
        'CNY': 'CCNI3M',
        'MYR': 'MRDRC',
        'TWD': 'NTDRC',
        'THB': 'TBDRC',
        'ARS': 'APDRC',
        'BRL': 'BCDRC',
        'CLP': 'CHDRC',
        'COP': 'CLDRC',
        'MXN': 'MPDRC',
        'PEN': 'PSDRC',
    }

    iso_country_dict = {'AUD': 'AU',
                        'BRL': 'BR',
                        'CAD': 'CA',
                        'CHF': 'CH',
                        'CLP': 'CL',
                        'CZK': 'CZ',
                        'EUR': 'EU',
                        'GBP': 'GB',
                        'HUF': 'HU',
                        'JPY': 'JP',
                        'KRW': 'KR',
                        'MXN': 'MX',
                        'NOK': 'NO',
                        'NZD': 'NZ',
                        'PHP': 'PH',
                        'PLN': 'PL',
                        'SEK': 'SE',
                        'SGD': 'SG',
                        'TRY': 'TR',
                        'TWD': 'TW',
                        'ZAR': 'ZA'}

    quoted_as_XXXUSD = ['BRL', 'CAD', 'CHF', 'CLP', 'CZK', 'HUF', 'JPY', 'KRW', 'MXN', 'NOK',
                        'PHP', 'PLN', 'SGD', 'TRY', 'TWD', 'ZAR', 'SEK']

    def __init__(self, ccy_symbol, start_date='1999-12-31', end_date='today'):
        """
        Returns an object with the following attributes:
            - spot_rate: Series with the spot rate data vs. the USD
            - deposit_rates: Series with the the currency deposit rate and the USD deposite rate
            - er_index: Series with the excess return index
            - ts_df: DataFrame with columns 'Spot', 'ccy_rate', and 'usd_rate'
        :param ccy_symbol: str, Currency symbol from Bloomberg
        :param start_date: str, when the tracker should start
        :param end_date: str, when the tracker should end
        """

        assert ccy_symbol in self.currencies, f'{ccy_symbol} not currently supported'

        self.bbg = BBG()
        self.ccy_symbol = ccy_symbol
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.spot_rate = self._get_spot_rate()
        self.deposit_rates = self._deposit_rates()

        self.country = self.iso_country_dict[self.ccy_symbol]
        self.fh_ticker = 'fx ' + self.country.lower() + ' ' + self.ccy_symbol.lower()
        self.df_metadata = self._get_metadata()

        self.df_tracker = self._calculate_tr_index(self.spot_rate, self.deposit_rates)
        self.df_tracker = self._get_tracker_melted()

    @staticmethod
    def _calculate_tr_index(spot_rate, dep_rates, ann_factor = 252):
        ts_df = pd.concat([spot_rate, dep_rates], axis=1, sort=True).fillna(method='ffill').dropna()

        er_index = pd.Series(index=ts_df.index)
        er_index.iloc[0] = 100.

        for d in er_index.index[1:]:
            fx_spot_ret = ts_df.loc[:d].iloc[-1,0] / ts_df.loc[:d].iloc[-2,0]

            # TODO check if all Bloomberg deposite rates are accrued in the same way
            long_carry_ret = 1 + (ts_df.loc[:d].iloc[-1,1] / 100) / ann_factor
            short_carry_ret = 1 + (ts_df.loc[:d].iloc[-1,2] / 100) / ann_factor
            carry_return = fx_spot_ret * long_carry_ret / short_carry_ret

            er_index[d] = er_index[:d].iloc[-2]*carry_return

        return er_index.to_frame('er_index')

    def _get_spot_rate(self):
        spot_rate_bbg_ticker = self.ccy_symbol + 'USD Curncy'
        bbg_raw_spot_data = self.bbg.fetch_series(securities=spot_rate_bbg_ticker,
                                                  fields='PX_LAST',
                                                  startdate=self.start_date,
                                                  enddate=self.end_date)
        bbg_raw_spot_data.columns = [self.ccy_symbol]
        bbg_raw_spot_data = bbg_raw_spot_data.fillna(method='ffill').dropna()
        return bbg_raw_spot_data

    def _deposit_rates(self):

        usd_dep_rate = self.bbg.fetch_series(securities='USDRC BDSR Curncy',
                                        fields='PX_LAST',
                                        startdate=self.start_date,
                                        enddate=self.end_date)
        usd_dep_rate.columns = ['usd_rate']

        if self.ccy_symbol not in ['RUB']:
            deposit_rate_bbg_ticker = self.deposit_rates_dict[self.ccy_symbol] + ' BDSR Curncy'
        else:
            deposit_rate_bbg_ticker = 'RRDRA Curncy' if self.ccy_symbol == 'RUB' else []

        ccy_dep_rate = self.bbg.fetch_series(securities=deposit_rate_bbg_ticker,
                                        fields='PX_LAST',
                                        startdate=self.start_date,
                                        enddate=self.end_date)
        ccy_dep_rate.columns = [self.ccy_symbol + '_rate']

        dep_rates = pd.concat([ccy_dep_rate,usd_dep_rate],join='outer',axis=1,sort=True).fillna(method='ffill').dropna()

        return dep_rates

    def _get_metadata(self):
        df = pd.DataFrame(index=[0],
                          data={'fh_ticker': self.fh_ticker,
                                'asset_class': 'FX',
                                'type': 'currency forward',
                                'exchange_symbol': self.ccy_symbol,
                                'currency': 'USD',
                                'country': self.country,
                                'maturity': 1/12})
        return df

    def _get_tracker_melted(self):
        df = self.df_tracker[['er_index']].rename({'er_index': self.fh_ticker}, axis=1)
        df['time_stamp'] = df.index.to_series()
        df = df.melt(id_vars='time_stamp', var_name='fh_ticker', value_name='value')
        df = df.dropna()
        return df
