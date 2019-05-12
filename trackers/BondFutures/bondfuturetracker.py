"""
This class is a work in progress
Author: Gustavo Amarante
"""

import math
import pandas as pd
from bloomberg import BBG
from pandas.tseries.offsets import BDay


class BuildBondFutureTracker(object):

    futures_ticker_dict = {'US': 'TY',
                           'GE': 'RX',
                           'FR': 'OAT',
                           'IT': 'IK',
                           'JP': 'JB',
                           'AU': 'XM',
                           'UK': 'G ',
                           'CA': 'CN'}

    fx_dict = {'GE': 'EURUSD Curncy',
               'UK': 'GBPUSD Curncy',
               'CA': 'CADUSD Curncy',
               'JP': 'JPYUSD Curncy',
               'AU': 'AUDUSD Curncy',
               'FR': 'EURUSD Curncy',
               'IT': 'EURUSD Curncy',
               'US': 'USD Curncy'}

    def __init__(self, country, start_date, end_date):

        self.bbg = BBG()
        self.country = country
        self.start_date = self._assert_date_type(start_date)
        self.end_date = self._assert_date_type(end_date)
        self.generic_tickers = [self.futures_ticker_dict[country] + str(x) + ' Comdty' for x in range(1, 4)]
        self.df_generics = self._get_generic_future_series()
        self.df_uc = self._get_underlying_contracts()
        self.contract_list = self._get_contracts_list()
        self.df_fn = self._get_first_notice_dates()
        self.df_prices = self._get_all_prices()
        df_tracker = self._build_tracker()
        self.tr_index = df_tracker[['er_index']]
        self.df_roll_info = df_tracker[['contract_rolling_out', 'roll_out_date', 'holdings']].dropna(how='any')

    def _get_generic_future_series(self):

        df = self.bbg.fetch_series(securities=self.generic_tickers,
                                   fields='PX_LAST',
                                   startdate=self.start_date,
                                   enddate=self.end_date)

        return df

    def _get_underlying_contracts(self):

        df = self.bbg.fetch_series(securities=self.generic_tickers,
                                   fields='FUT_CUR_GEN_TICKER',
                                   startdate=self.start_date,
                                   enddate=self.end_date)

        df = df.reindex(self.df_generics.index).fillna(method='ffill')

        return df

    def _get_contracts_list(self):

        contract_list = self.bbg.fetch_futures_list(generic_ticker=self.futures_ticker_dict[self.country] + '1 Comdty')

        return contract_list

    def _get_first_notice_dates(self):

        df = self.bbg.fetch_contract_parameter(securities=self.contract_list,
                                               field='FUT_NOTICE_FIRST').sort_values('FUT_NOTICE_FIRST')

        return df

    def _get_all_prices(self):

        tickers = self.contract_list + [self.fx_dict[self.country]]

        df = self.bbg.fetch_series(securities=tickers,
                                   fields='PX_LAST',
                                   startdate=self.start_date,
                                   enddate=self.end_date)

        df = df.reindex(self.df_generics.index).fillna(method='ffill')

        return df

    def _build_tracker(self):

        df_tracker = pd.DataFrame(index=self.df_generics.index,
                                  columns=['contract_rolling_out', 'er_index', 'roll_out_date', 'holdings'])

        # set the values for the initial date
        dt_ini = self.df_uc.index[0]
        df_tracker.loc[dt_ini, 'er_index'] = 100
        contract_rolling_out = self.df_uc.loc[dt_ini, self.futures_ticker_dict[self.country] + '2 Comdty'] + ' Comdty'
        df_tracker.loc[dt_ini, 'contract_rolling_out'] = contract_rolling_out
        holdings = df_tracker.loc[dt_ini, 'er_index'] / (self.df_generics.loc[dt_ini, self.futures_ticker_dict[self.country] + '2 Comdty'] * self.df_prices[self.fx_dict[self.country]].loc[dt_ini])
        df_tracker.loc[dt_ini, 'holdings'] = holdings
        roll_out_date = self.df_fn.loc[df_tracker.loc[dt_ini, 'contract_rolling_out'], 'FUT_NOTICE_FIRST'] - BDay(1)
        df_tracker.loc[dt_ini, 'roll_out_date'] = roll_out_date

        for d, dm1 in zip(df_tracker.index[1:], df_tracker.index[:-1]):

            df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out

            price_dm1 = self.df_prices.loc[dm1, contract_rolling_out]
            price_d = self.df_prices.loc[d, contract_rolling_out]
            pnl = holdings * (price_d - price_dm1) * self.df_prices[self.fx_dict[self.country]].loc[d]

            if math.isnan(pnl):
                pnl = 0

            df_tracker.loc[d, 'er_index'] = df_tracker.loc[dm1, 'er_index'] + pnl

            if d >= roll_out_date.date():
                contract_rolling_out = (self.df_uc.loc[d, self.futures_ticker_dict[self.country] + '2 Comdty'] + ' Comdty')
                df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out

                holdings = df_tracker.loc[d, 'er_index'] / (self.df_generics.loc[d, self.futures_ticker_dict[self.country] + '2 Comdty'] * self.df_prices[self.fx_dict[self.country]].loc[d])
                df_tracker.loc[d, 'holdings'] = holdings

                roll_out_date = self.df_fn.loc[df_tracker.loc[d, 'contract_rolling_out'], 'FUT_NOTICE_FIRST'] - BDay(1)
                df_tracker.loc[d, 'roll_out_date'] = roll_out_date

        return df_tracker

    @staticmethod
    def _assert_date_type(date):

        if type(date) is pd.Timestamp:
            date = date
        else:
            date = pd.to_datetime(date)

        return date


"""
TO DO
* number of rolling days
* start roll days before the first notice
* include roll cost
* Is there a way to grab the initial and last date from bbg? So that the date arguments could be optional.
* Method to update the AWS database
"""
