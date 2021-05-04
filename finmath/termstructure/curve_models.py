"""
Author: Gustavo Soares
"""

from typing import Union, Collection, Optional, Tuple
import pandas as pd
import numpy as np
from calendars import DayCounts
from calendars.custom_date_types import Date, TODAY
import scipy.optimize as opt
import warnings

ANBIMA_LAMBDAS = np.array([2.2648, 0.3330])


def forward_rate(t1: float, t2: float, zero_curve: pd.Series) -> float:
    t1, t2 = sorted([t1, t2])
    y1 = flat_forward_interpolation(t1, zero_curve)
    y2 = flat_forward_interpolation(t2, zero_curve)

    return (((1. + y2) ** t2) / ((1. + y1) ** t1)) ** (1 / (t2 - t1)) - 1.


def _clean_curve(curve: pd.Series,
                 dc: Optional[DayCounts] = None,
                 ref_date: Optional[Date] = None) -> pd.Series:
    date_types = list(Date.__args__) + [pd.Timestamp]

    if all([type(t) in date_types for t in curve.index]):
        msg = 'Parameter ref_date as Date required!'
        assert type(ref_date) in date_types, msg
        assert dc is not None, 'Parameter dc as DayCounts required!'
        dates = [dc.tf(pd.to_datetime(ref_date).date(), t) for t in curve.index]
        clean_curve = pd.Series(curve.values, dates).astype(float)
    else:
        clean_curve = pd.Series(curve.values,
                                [float(t) for t in curve.index]).astype(float)

    return clean_curve.dropna().sort_index()


def flat_forward_interpolation(t: Union[float, Date],
                               zero_curve: pd.Series,
                               dc: Optional[DayCounts] = None,
                               ref_date: Optional[Date] = None) -> float:
    if isinstance(t, float) or isinstance(t, int):
        t = float(t)
        clean_curve = _clean_curve(zero_curve)
    else:
        if type(dc) is not DayCounts:
            msg = f'Parameter t as Date requires parameter dc as DayCounts'
            raise TypeError(msg)
        if type(ref_date) not in Date.__args__ + [pd.Timestamp]:
            msg = f'Parameter t as Date requires parameter ref_date as Date'
            raise TypeError(msg)
        else:
            t = dc.tf(pd.to_datetime(ref_date).date(), t)
            clean_curve = _clean_curve(zero_curve, dc=dc, ref_date=ref_date)

        t = float(t)

    zero_curve = clean_curve.dropna().sort_index()
    t0 = min(zero_curve.index)
    tn = max(zero_curve.index)
    if t <= t0:
        y = zero_curve[t0]
    elif t >= tn:
        y = zero_curve[tn]
    else:
        t1, y1 = [(x, y) for x, y in zero_curve.items() if x < t][-1]
        t2, y2 = [(x, y) for x, y in zero_curve.items() if x > t][0]
        y = ((1. + y1) ** ((t1 / t) * (t2 - t) / (t2 - t1))) * \
            ((1. + y2) ** ((t2 / t) * (t - t1) / (t2 - t1))) - 1

    return y


class NelsonSiegelSvensson(object):

    def __init__(self,
                 prices: Union[float, Collection[float]],
                 cash_flows: Union[pd.Series, Collection[pd.Series]],
                 day_count_convention: str = 'bus/252',
                 calendar: str = 'cdr_anbima',
                 ref_date: Date = TODAY,
                 lambdas: Optional[np.array] = ANBIMA_LAMBDAS):

        if isinstance(prices, float):
            prices = [prices]

        if isinstance(cash_flows, pd.Series):
            cash_flows = [cash_flows]

        self.ref_date = ref_date
        self.dc = DayCounts(dc=day_count_convention, calendar=calendar)

        self.lambdas = np.ones(2) if lambdas is None else lambdas
        self.betas = self.estimate_betas(prices=prices,
                                         cash_flows=cash_flows,
                                         dc=self.dc,
                                         ref_date=self.ref_date,
                                         lambdas=self.lambdas)

    @staticmethod
    def rate_for_ytm(betas=np.zeros(4),
                     lambdas=ANBIMA_LAMBDAS,
                     ytm: float = 1.):

        l1 = lambdas[0]
        first_exp_term = lambda x: (1. - np.exp(-l1 * x)) / (l1 * x)
        y = betas[0] + betas[1] * first_exp_term(ytm)
        sec_exp_term = lambda x: first_exp_term(x) - np.exp(-l1 * x)
        y += betas[2] * sec_exp_term(ytm)
        l2 = lambdas[1]
        first_exp_term_II = lambda x: (1. - np.exp(-l2 * x)) / (l2 * x)
        sec_exp_term_II = lambda x: first_exp_term_II(x) - np.exp(-l2 * x)
        y += betas[3] * sec_exp_term_II(ytm)

        return y

    def bond_price(self,
                   cf: pd.Series,
                   dc: Optional[DayCounts] = None,
                   ref_date: Optional[Date] = None,
                   betas: Optional[np.array] = None,
                   lambdas: Optional[np.array] = None):

        if dc is None:
            assert hasattr(self, 'dc'), 'No day count parameter dc!'
            dc = self.dc

        if ref_date is None:
            assert hasattr(self, 'ref_date'), 'No ref_date parameter!'
            ref_date = self.ref_date

        if betas is None:
            if hasattr(self, 'betas'):
                betas = self.betas
            else:
                betas = np.zeros(4)

        if lambdas is None:
            if hasattr(self, 'lambdas'):
                lambdas = self.lambdas
            else:
                lambdas = ANBIMA_LAMBDAS

        pv = 0.
        for d, dpay in cf.items():
            ytm = dc.tf(ref_date, d)
            y = self.rate_for_ytm(betas=betas, lambdas=lambdas, ytm=ytm)
            pv += dpay / ((1. + y) ** ytm)
        return pv

    def price_errors(self,
                     prices: Union[float, Collection[float]],
                     cash_flows: Union[pd.Series, Collection[pd.Series]],
                     dc: Optional[DayCounts] = None,
                     ref_date: Optional[Date] = None,
                     betas: Optional[np.array] = None,
                     lambdas: Optional[np.array] = None):

        msg = 'Not the same number of prices as cash flows!'
        assert len(prices) == len(cash_flows), msg

        if dc is None:
            assert hasattr(self, 'dc'), 'No day count parameter dc!'
            dc = self.dc

        if ref_date is None:
            assert hasattr(self, 'ref_date'), 'No ref_date parameter!'
            ref_date = self.ref_date

        pe = 0.
        for p, cf in zip(prices, cash_flows):
            theoretical_price = self.bond_price(cf, dc,
                                                ref_date=ref_date,
                                                betas=betas,
                                                lambdas=lambdas)
            w = 1 / dc.tf(ref_date, max(cf.index))  # TODO: change to duration
            pe += w * ((p - theoretical_price) / p) ** 2.

        return pe

    def estimate_betas(self,
                       prices: Union[float, Collection[float]],
                       cash_flows: Union[pd.Series, Collection[pd.Series]],
                       dc: Optional[DayCounts],
                       ref_date: Optional[Date],
                       lambdas=Optional[np.array]
                       ):

        obj_function = lambda x: self.price_errors(prices=prices,
                                                   cash_flows=cash_flows,
                                                   dc=dc,
                                                   ref_date=ref_date,
                                                   betas=x,
                                                   lambdas=lambdas)

        x0 = np.zeros(4)
        res = opt.minimize(obj_function, x0, method='SLSQP')

        if not res['message'] == 'Optimization terminated successfully.':
            raise ArithmeticError('Optimization convergence may have failed!')

        return res.x


class CurveBootstrap(object):

    def __init__(self,
                 cash_flows: Collection[pd.Series],
                 rates: Optional[Union[float, Collection[float]]] = None,
                 prices: Optional[Union[float, Collection[float]]] = None,
                 day_count_convention: str = 'bus/252',
                 calendar: str = 'cdr_anbima',
                 ref_date: Date = TODAY):

        msg = 'Parameters rates and prices cannot be both None!'
        assert rates is not None or prices is not None, msg

        msg = 'Parameter cash_flows needs to be a Collection of Pandas Series!'
        assert all(map(lambda x: isinstance(x, pd.Series), cash_flows)), msg

        if rates is not None and isinstance(rates, float):
            rates = [rates]

        if prices is not None and isinstance(prices, float):
            prices = [prices]

        if rates is not None and prices is not None:
            msg = 'Both parameters rates and prices given, dropping prices!'
            warnings.warn(msg)
            prices = None

        self.ref_date = ref_date
        self.dc = DayCounts(dc=day_count_convention, calendar=calendar)

        self.zero_curve = self._initial_zero_curve(cash_flows=cash_flows,
                                                   rates=rates,
                                                   prices=prices,
                                                   dc=self.dc,
                                                   ref_date=self.ref_date)

        self.bootstrap(cash_flows=cash_flows,
                       rates=rates,
                       prices=prices)

    @staticmethod
    def _initial_zero_curve(cash_flows: Collection[pd.Series],
                            rates: Optional[Collection[float]] = None,
                            prices: Optional[Collection[float]] = None,
                            dc: Optional[DayCounts] = None,
                            ref_date: Optional[Date] = None) -> pd.Series:

        if rates is not None:
            bonds = zip(cash_flows, rates)
            isrates = True
            if prices is not None:
                msg = 'Both parameters rates and prices given, dropping prices!'
                warnings.warn(msg)
                del prices
        else:
            bonds = zip(cash_flows, prices)
            isrates = False

        ytm = []
        curve = []
        for cf, y in bonds:
            if len(cf) == 1:
                d = pd.to_datetime(cf.index[-1]).date()
                t = dc.tf(ref_date, d)

                if isrates:
                    r = float(y)
                else:
                    r = (cf.iloc[-1] / float(y)) ** (1. / t) - 1.

                ytm += [t]
                curve += [r]

        return pd.Series(index=ytm, data=curve).sort_index()

    def rate_for_date(self, t: Union[float, Date]) -> float:

        y = flat_forward_interpolation(t=t,
                                       zero_curve=self.zero_curve,
                                       dc=self.dc,
                                       ref_date=self.ref_date)
        return y

    @staticmethod
    def _bond_pv_for_rate(expanded_rate: float,
                          zero_curve: pd.Series,
                          bond_cash_flows: pd.Series,
                          dc: Optional[DayCounts] = None,
                          ref_date: Optional[Date] = None) -> float:

        zero_curve_end = max(zero_curve.index)
        ytm = dc.tf(ref_date, max(bond_cash_flows.index))
        expanded_point = pd.Series(index=[ytm], data=expanded_rate)
        zero_curve = zero_curve.append(expanded_point).sort_index().copy()

        pv = 0.
        for d, c in bond_cash_flows.items():
            t = dc.tf(ref_date, d)
            if t > zero_curve_end:
                y = flat_forward_interpolation(t=t,
                                               zero_curve=zero_curve,
                                               dc=dc,
                                               ref_date=ref_date)
                pv += c / (1. + y) ** t

        return pv

    @staticmethod
    def _bond_strip(zero_curve: pd.Series,
                    bond_cash_flows: pd.Series,
                    dc: Optional[DayCounts] = None,
                    ref_date: Optional[Date] = None,
                    rate: Optional[float] = None,
                    price: Optional[float] = None) -> Tuple[float,
                                                            float,
                                                            pd.Series]:

        msg = 'Parameters rate and price cannot be both None!'
        assert rate is not None or price is not None, msg

        msg = 'Bond maturity is shorter than given zero curve!'
        maturity = dc.tf(ref_date, max(bond_cash_flows.index))
        zero_curve_end = max(zero_curve.index)
        assert zero_curve_end <= maturity, msg

        if price is not None:
            price = float(price)
            if rate is not None:
                msg = 'Both parameters rate and price given, dropping rate!'
                warnings.warn(msg)
                del rate
        else:
            price = 0.
            for d, c in bond_cash_flows.items():
                ytm = dc.tf(ref_date, d)
                price += c / (1. + rate) ** ytm

        pv = 0.

        for d, c in bond_cash_flows.sort_index().items():
            t = dc.tf(ref_date, d)
            if t <= zero_curve_end:
                y = flat_forward_interpolation(t=t,
                                               zero_curve=zero_curve,
                                               dc=dc,
                                               ref_date=ref_date)
                pv += c / (1. + y) ** t

        return price, pv, maturity

    def _expand_zero_curve(self,
                           bond_cash_flows: pd.Series,
                           rate: Optional[float] = None,
                           price: Optional[float] = None):

        price, pv, ytm = self._bond_strip(
            zero_curve=self.zero_curve,
            bond_cash_flows=bond_cash_flows,
            dc=self.dc,
            ref_date=self.ref_date,
            rate=rate,
            price=price)

        price_given_rate = lambda x: self._bond_pv_for_rate(
            expanded_rate=x,
            zero_curve=self.zero_curve,
            bond_cash_flows=bond_cash_flows,
            dc=self.dc,
            ref_date=self.ref_date) + pv

        pct_error = lambda x: (price - price_given_rate(x)) / price
        obj_fun = lambda x: pct_error(x) ** 2.
        x0 = self.zero_curve.iloc[-1]
        res = opt.minimize(obj_fun, x0, method='SLSQP')
        if not res['message'] == 'Optimization terminated successfully.':
            raise ArithmeticError('Optimization convergence may have failed!')

        expanded_point = pd.Series(index=[ytm], data=res.x)

        return self.zero_curve.append(expanded_point).sort_index()

    def bootstrap(self,
                  cash_flows: Collection[pd.Series],
                  rates: Optional[Collection[float]] = None,
                  prices: Optional[Collection[float]] = None):

        msg = 'Parameters rates and prices cannot be both None!'
        assert rates is not None or prices is not None, msg

        tmax = max(self.zero_curve.index)
        for i in range(len(cash_flows)):
            cf = list(cash_flows)[i]
            if len(cf) > 1 and self.dc.tf(self.ref_date, max(cf.index)) > tmax:
                if rates is None or list(rates)[i] is None:
                    new_curve = self._expand_zero_curve(bond_cash_flows=cf,
                                                        rate=None,
                                                        price=list(prices)[i])
                elif prices is None or list(prices)[i] is None:
                    new_curve = self._expand_zero_curve(bond_cash_flows=cf,
                                                        rate=list(rates)[i],
                                                        price=None)
                else:
                    continue
                self.zero_curve = new_curve
            else:
                continue
