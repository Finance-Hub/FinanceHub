"""
Author: Gustavo Amarante
"""

import pandas as pd
import numpy as np
from datetime import date
from calendars import DayCounts



class B3AbstractDerivative(object):

    monthdict = {'F': 1, 'G': 2, 'H': 3, 'J':  4, 'K':  5, 'M':  6,
                 'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12}

    calendar = None
    contract = None
    dc_convention = None
    pilar_day = None
    roll_method = None

    def __init__(self, db_connect):
        self.conn = db_connect
        self.time_series = self._get_time_series()
        self.dc = DayCounts(dc=self.dc_convention, calendar=self.calendar)

    def time_menu(self, code=None):
        """
        Gets all of the available trading dates for the contract in 'code'.
        If 'code' is None, all dates are returned.
        :param code: str with the contract code
        :return: list of timestamps
        """
        if code is None:
            tm = self.time_series.index.levels[0]
        else:
            tm = self.time_series.index.get_loc_level(code, 1)[1]

        return list(tm)

    def market_menu(self, t=None):
        """
        Gets all of the available contracts codes for date 't'.
        If 't' is None, all contract codes are returned.
        :param t: any format accepted by pandas.to_datetime()
        :return: list of contract codes
        """
        if t is None:
            mm = self.time_series.index.levels[1]
        else:
            t = pd.to_datetime(t)
            mm = self.time_series.index.get_loc_level(t, 0)[1]

        return list(mm)

    def maturity(self, code):
        """
        Given a contract code, returns the timestamp of the maturity date.
        THIS FUNCTION WILL BREAK WHEN CONTRACTS MATURE IN 2092 START TRADING
        :param code: str with contract code
        :return: tuple (year, month)
        """
        month = self.monthdict[code.upper()[0]]
        year = int(code.upper()[1:])

        if year >= 92:
            year = year + 1900
        else:
            year = year + 2000

        mat_date = date(year, month, self.pilar_day)
        mat_date = self.dc.busdateroll(mat_date, self.roll_method)
        return mat_date

    def du2maturity(self, t, code):
        """
        returns the number of business days between t and the maturity date of the contract
        :param t: current date
        :param code: contract code
        :return: int
        """
        mat_date = self.maturity(code)
        du = self.dc.days(t, mat_date)
        return du

    def dc2maturity(self, t, code):
        """
        returns the number of actual days between t and the maturity date of the contract, independent
        of the daycount convention
        :param t: current date
        :param code: contract code
        :return: int
        """
        mat_date = self.maturity(code)
        du = self.dc.daysnodc(t, mat_date)
        return du

    def volume(self, code, t=None):
        """
        returns the trading volume. If 't' is None, returns a pandas Series of the volume of 'code'.
        """
        if t is None:
            filter_contract = self.time_series.index.get_loc_level(code, 1)[0]
            v = self.time_series[filter_contract]['trading_volume'].droplevel(1)
        else:
            v = self.time_series['trading_volume'].loc[t, code]

        return v

    def open_interest(self, code, t=None):
        """
        returns the open interest at the close of date 't'.
        If 't' is None, returns a pandas Series of the volume of 'code'.
        """
        if t is None:
            filter_contract = self.time_series.index.get_loc_level(code, 1)[0]
            v = self.time_series[filter_contract]['open_interest_close'].droplevel(1)
        else:
            v = self.time_series['open_interest_close'].loc[t, code]

        return v

    def pnl(self):
        # TODO implement (precisa da série do CDI, mas acho que da pra pegar com a API do SGS)
        pass

    def build_df(self):
        # TODO implement
        return

    def filter(self):
        # TODO implement
        pass

    def _get_time_series(self):
        """
        Fetches the whole database for the given contract
        """

        sql_query = self._time_series_query()

        df = pd.read_sql(sql=sql_query,
                         con=self.conn.connection,
                         parse_dates={'time_stamp': '%Y-%m-%d'})

        df = df.set_index(['time_stamp', 'maturity_code'])

        return df

    def _time_series_query(self):

        sql_query = f'SELECT TIME_STAMP, MATURITY_CODE, OPEN_INTEREST_OPEN, OPEN_INTEREST_CLOSE, ' \
                    f'NUMBER_OF_TRADES, TRADING_VOLUME, FINANCIAL_VOLUME, PREVIOUS_SETTLEMENT, ' \
                    f'INDEXED_SETTLEMENT, OPENING_PRICE, MINIMUM_PRICE, MAXIMUM_PRICE, AVERAGE_PRICE, ' \
                    f'LAST_PRICE, SETTLEMENT_PRICE, LAST_BID, LAST_OFFER FROM "B3futures" ' \
                    f'WHERE CONTRACT=\'{self.contract}\' ORDER BY(TIME_STAMP, MATURITY_CODE);'

        return sql_query


class DI1(B3AbstractDerivative):
    calendar = 'anbima'
    contract = 'DI1'
    dc_convention = 'BUS/252'
    pilar_day = 1
    roll_method = 'forward'

    def implied_yield(self, code, t=None):
        """
        returns the quote at the close of date 't'.
        If 't' is None, returns a pandas Series of the quotes for 'code'.
        """

        if t is None:
            filter_contract = self.time_series.index.get_loc_level(code, 1)[0]
            y = self.time_series[filter_contract]['last_price'].droplevel(1)
        else:
            y = self.time_series['last_price'].loc[t, code]

        return y/100

    def theoretical_price(self, code, t):
        """
        compute the theoretical price based on the last quote of date t.
        :param code: contract code
        :param t: reference date
        """
        y = self.implied_yield(code, t)
        du = self.du2maturity(t, code)
        price = 100000 / ((1 + y)**(du/252))
        return price

    def dv01(self, code, t):
        """
        compute the dv01 based on the last quote of date t.
        :param code: contract code
        :param t: reference date
        """
        du = self.du2maturity(t, code)
        y = self.implied_yield(code, t)
        pu = self.theoretical_price(code, t)
        dPdy = pu * (-du/252) / (1 + y)
        dv01 = dPdy/10000  # changes to 1bp move
        return dv01

    def duration(self, code, t):
        """
        compute the duration based on the last quote of date t.
        :param code: contract code
        :param t: reference date
        """
        dPdy = 10000 * self.dv01(code, t)
        duration = dPdy / self.theoretical_price(code, t)
        return duration

    def convexity(self, code, t):
        """
        compute the convexity based on the last quote of date t.
        :param code: contract code
        :param t: reference date
        """
        du = self.du2maturity(t, code)
        y = self.implied_yield(code, t) / 100.
        dPdy2 = 100000 * (du / 252) * (du / 252 + 1) / ((1 + y) ** (du / 252 + 2))
        return dPdy2/self.theoretical_price(code, t)

    def curve(self, t):
        """
        returns the di curve at the close of date 't'.
        :param t: reference date or list of valid settlement dates
        """

        curve = self.time_series.loc[t, 'last_price']

        if isinstance(curve.index, pd.MultiIndex):
            d_and_m_tuples = [(d, self.maturity(c)) for d,c in curve.index]
            curve.index = pd.MultiIndex.from_tuples(d_and_m_tuples,
                                            names=['time_stamp', 'maturity'])
        else:
            curve.index = [self.maturity(c) for c in curve.index]
            curve.index.name = 'maturity'

        curve = curve[curve>0].sort_index().astype(float)

        return curve

    def discount_factor(self, code, t):
        """
        returns the discount factor at the close of date 't'.
        """
        y = self.time_series['last_price'].loc[t, code]
        du = self.du2maturity(t, code)
        df = 1 / ((1 + y / 100.) ** (du/252))
        return df

    def interpolated_yield(self, m, t):
        """
        returns the Piecewise Flat Forward Rate (Andersen and Piterbarg,
        2010) for date 'm' at the close of date 't'.
        """

        curve = self.curve(t)

        t1 = max([x for x in curve.index if x<=m])
        t2 = min([x for x in curve.index if x>=m])

        if t1<t2:
            y1, y2 = np.log(1. + curve[t1]), np.log(1 + curve[t2])
            t1, t2 = self.dc.days(t, t1) / 252., self.dc.days(t, t2) / 252.

            x = self.dc.days(t, m) / 252.
            y = t1 * y1 + (x - t1) / (t2 - t1) * (t2 * y2 - t1 * y1)
            y = np.exp(y / x)
        else:
            y = curve[m]

        return y