"""
Author: Gustavo Soares
"""

import math
import pandas as pd
from bloomberg import BBG
from pandas.tseries.offsets import BDay
from datetime import timedelta


class CommFutureTracker(object):
    """
    Class for creating excess return indices for commodity futures using data from bloomberg.
    A default front-month roll schedule is assumed but it can be provided by the user
    At the start date, we assume we trade 100 units of the commodity in the contract defined by the roll schedule
    We MtM the position over the month and then roll it into the next contracts as defined by the roll schedule
    """

    # Currently available commodities
    # TODO add other commodities to this dictionary
    roll_schedule_dict = {
        'CL': ['H', 'K', 'K', 'N', 'N', 'U', 'U', 'X', 'X', 'F+', 'F+', 'H+'],
    }

    def __init__(self, comm_bbg_code, start_date = '2004-01-05', end_date = 'today',
                 roll_schedule = None, roll_start_bday = 5, roll_window_size = 5):

        if comm_bbg_code in self.roll_schedule_dict.keys():
            self.roll_schedule = self.roll_schedule_dict[comm_bbg_code]
        elif roll_schedule:
            self.roll_schedule = roll_schedule
        else:
            raise KeyError('Commodity not yet supported, please include roll schedule for %s' % comm_bbg_code)

        self.comm_bbg_code = comm_bbg_code
        self.roll_start_bday = roll_start_bday
        self.roll_window_size = roll_window_size
        self.start_date = (pd.to_datetime(start_date) + BDay(1)).date()  # for the data
        self.end_date = pd.to_datetime(end_date).date()

        self._grab_bbg_data()
        self._initialize()
        self._calculate_tr_index()



    def _grab_bbg_data(self):
        bbg = BBG()
        self.contract_list = bbg.fetch_futures_list(generic_ticker=self.comm_bbg_code + '1 Comdty')
        self.first_notice_dates = bbg.fetch_contract_parameter(securities=self.contract_list,
                                                  field='FUT_NOTICE_FIRST').sort_values('FUT_NOTICE_FIRST')

        # Grab all contract series
        df_prices = bbg.fetch_series(securities=self.contract_list,
                                     fields='PX_LAST',
                                     startdate=self.start_date,
                                     enddate=self.end_date)
        self.prices = df_prices.fillna(method='ffill')

    def _initialize(self):
        # start on 1st bday of month
        back_start_date = self.prices.loc[self.prices.index[0].replace(day=28) +
                                               timedelta(days=4):].index[0]

        self._get_contracts_for_date(back_start_date)
        self._get_contract_weights(back_start_date)
        self.price_out = self.prices.loc[back_start_date, self.contract_rolling_out]
        self.price_in = self.prices.loc[back_start_date, self.contract_rolling_in]

        df_tracker = pd.DataFrame(index=self.prices.loc[back_start_date:].index,
                                  columns=['contract_rolling_out', 'contract_rolling_in',
                                           'price_out_today', 'price_in_today', 'price_out_yst', 'price_in_yst',
                                           'w_out', 'w_in',
                                           'holdings_out', 'holdings_in',
                                           'er_index'])

        df_tracker.loc[back_start_date, 'er_index'] = 100

        df_tracker.loc[back_start_date, 'contract_rolling_out'] = self.contract_rolling_out
        df_tracker.loc[back_start_date, 'contract_rolling_in'] = self.contract_rolling_in
        df_tracker.loc[back_start_date, 'price_out_today'] = self.price_out
        df_tracker.loc[back_start_date, 'price_in_today'] = self.price_in
        df_tracker.loc[back_start_date, 'w_out'] = self.weight_out
        df_tracker.loc[back_start_date, 'w_in'] = self.weight_in

        holdings_out = self.weight_out * df_tracker.loc[back_start_date, 'er_index'] / self.price_out
        holdings_in = self.weight_in * df_tracker.loc[back_start_date, 'er_index'] / self.price_in
        self.holdings_out = 0 if math.isnan(holdings_out) else holdings_out
        self.holdings_in = 0 if math.isnan(holdings_in) else holdings_in

        df_tracker.loc[back_start_date, 'holdings_out'] = self.holdings_out
        df_tracker.loc[back_start_date, 'holdings_in'] = self.holdings_in

        self.df_tracker = df_tracker

    def _get_contracts_for_date(self,d):
        month_letter = self.roll_schedule[d.month - 1] if self.roll_schedule[d.month - 1].find('+') == -1 else \
                                                            self.roll_schedule[d.month - 1][0]
        year_int = d.year if self.roll_schedule[d.month - 1].find('+') == -1 else d.year + 1
        contract_rolling_out = self.comm_bbg_code + month_letter + str(year_int)[-2:] + ' Comdty'
        if contract_rolling_out not in self.contract_list:
            contract_rolling_out = self.comm_bbg_code + month_letter + str(year_int)[-1] + ' Comdty'

        d2 = d.replace(day=28) + timedelta(days=4)
        month_letter = self.roll_schedule[d2.month - 1] if self.roll_schedule[d2.month - 1].find('+') == -1 else \
                                            self.roll_schedule[d2.month - 1][0]
        year_int = d2.year if self.roll_schedule[d2.month - 1].find('+') == -1 else d2.year + 1
        contract_rolling_in = self.comm_bbg_code + month_letter + str(year_int)[-2:] + ' Comdty'
        if contract_rolling_in not in self.contract_list:
            contract_rolling_in = self.comm_bbg_code + month_letter + str(year_int)[-1] + ' Comdty'
        self.contract_rolling_out = contract_rolling_out
        self.contract_rolling_in = contract_rolling_in

    def _get_contract_weights(self, d, roll_type='standard'):
        days_in_the_month = [x for x in self.prices.index if x.month == d.month and x.year == d.year]
        if roll_type == 'standard':
            start_idx = self.roll_start_bday - 1
            end_idx = self.roll_start_bday + self.roll_window_size - 2
            roll_start_date = days_in_the_month[start_idx] if len(days_in_the_month) > start_idx else days_in_the_month[
                -1]
            roll_end_date = days_in_the_month[end_idx] if len(days_in_the_month) > end_idx else days_in_the_month[-1]
        elif roll_type == 'backward_from_month_end':
            roll_start_date = days_in_the_month[self.roll_start_bday]
            roll_end_date = days_in_the_month[-1]

        if d < roll_start_date:
            weight_out = 1
        elif d > roll_end_date:
            weight_out = 0
        else:
            weight_out = float(len([x for x in days_in_the_month if x > d
                                    and x <= roll_end_date])) / float(self.roll_window_size )
        self.weight_out = weight_out
        self.weight_in = 1 - weight_out

    def _calculate_tr_index(self):
        for d, dm1 in zip(self.df_tracker.index[1:], self.df_tracker.index[:-1]):

            self.df_tracker.loc[d, 'w_out'] = self.weight_out
            self.df_tracker.loc[d, 'w_in'] = self.weight_in

            self.df_tracker.loc[d, 'contract_rolling_out'] = self.contract_rolling_out
            self.df_tracker.loc[d, 'contract_rolling_in'] = self.contract_rolling_in

            price_out_d = self.prices.loc[:d,self.contract_rolling_out].iloc[-1]
            price_out_dm1 = self.prices.loc[:d,self.contract_rolling_out].iloc[-2]
            price_in_d = self.prices.loc[:d,self.contract_rolling_in].iloc[-1]
            price_in_dm1 = self.prices.loc[:d,self.contract_rolling_in].iloc[-2]

            self.df_tracker.loc[d, 'price_out_today'] = price_out_d
            self.df_tracker.loc[d, 'price_in_today'] = price_in_d

            self.df_tracker.loc[d, 'price_out_yst'] = price_out_dm1
            self.df_tracker.loc[d, 'price_in_yst'] = price_in_dm1

            self.df_tracker.loc[d, 'holdings_out'] = self.holdings_out
            self.df_tracker.loc[d, 'holdings_in'] = self.holdings_in

            if self.weight_in == 1:
                pnl = self.holdings_in * (price_in_d - price_in_dm1)
            else:
                pnl = self.holdings_in * (price_in_d - price_in_dm1) + self.holdings_out * (price_out_d - price_out_dm1)

            self.df_tracker.loc[d, 'er_index'] = self.df_tracker.loc[dm1, 'er_index'] + pnl

            self._get_contracts_for_date(d)

            if d.month != dm1.month:
                self.holdings_out = self.holdings_in
                self.holdings_in = 0
                self.weight_out = 1
                self.weight_in = 0

                price_out_d = self.prices.loc[:d, self.contract_rolling_out].iloc[-1]
                price_out_dm1 = self.prices.loc[:d, self.contract_rolling_out].iloc[-2]
                price_in_d = self.prices.loc[:d, self.contract_rolling_in].iloc[-1]
                price_in_dm1 = self.prices.loc[:d, self.contract_rolling_in].iloc[-2]

                self.df_tracker.loc[d, 'holdings_out'] = self.holdings_out
                self.df_tracker.loc[d, 'holdings_in'] = self.holdings_in
                self.df_tracker.loc[d, 'w_out'] = self.weight_out
                self.df_tracker.loc[d, 'w_in'] = self.weight_in
                self.df_tracker.loc[d, 'price_out_today'] = price_out_d
                self.df_tracker.loc[d, 'price_in_today'] = price_in_d
                self.df_tracker.loc[d, 'price_out_yst'] = price_out_dm1
                self.df_tracker.loc[d, 'price_in_yst'] = price_in_dm1
                self.df_tracker.loc[d, 'contract_rolling_out'] = self.contract_rolling_out
                self.df_tracker.loc[d, 'contract_rolling_in'] = self.contract_rolling_in

            else:
                self._get_contract_weights(d)

                holdings_out = self.weight_out * self.df_tracker.loc[d, 'er_index'] / price_out_d
                holdings_in = self.weight_in * self.df_tracker.loc[d, 'er_index'] / price_in_d
                self.holdings_out = 0 if math.isnan(holdings_out) else holdings_out
                self.holdings_in = 0 if math.isnan(holdings_in) else holdings_in
