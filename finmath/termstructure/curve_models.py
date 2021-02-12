"""
Author: Gustavo Soares
"""
from typing import Union, Collection, Optional
import pandas as pd
import numpy as np
from calendars import DayCounts
from calendars.custom_date_types import Date, TODAY
import scipy.optimize as opt

ANBIMA_LAMBDAS = np.array([2.2648, 0.3330])

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
                                         lambdas = self.lambdas)

    @staticmethod
    def rate_for_ytm(betas = np.zeros(4),
                     lambdas = ANBIMA_LAMBDAS,
                     ytm: float = 1.):

        l1 = lambdas[0]
        first_exp_term = lambda x : (1. - np.exp(-l1 * x)) / (l1 * x)
        y = betas[0] + betas[1] * first_exp_term(ytm)
        sec_exp_term = lambda x : first_exp_term(x) - np.exp(-l1 * x)
        y += betas[2] * sec_exp_term(ytm)
        l2 = lambdas[1]
        first_exp_term_II = lambda x : (1. - np.exp(-l2 * x)) / (l2 * x)
        sec_exp_term_II = lambda x : first_exp_term_II(x) - np.exp(-l2 * x)
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
            w = 1/ dc.tf(ref_date, max(cf.index)) #TODO: change to duration
            pe += w * ((p - theoretical_price)/p) ** 2.

        return pe

    def estimate_betas(self,
                       prices: Union[float, Collection[float]],
                       cash_flows: Union[pd.Series, Collection[pd.Series]],
                       dc: Optional[DayCounts],
                       ref_date: Optional[Date],
                       lambdas = Optional[np.array]
                       ):


        obj_function = lambda x : self.price_errors(prices=prices,
                                                    cash_flows=cash_flows,
                                                    dc=dc,
                                                    ref_date=ref_date,
                                                    betas=x,
                                                    lambdas = lambdas)

        x0 = np.zeros(4)
        res = opt.minimize(obj_function, x0, method='SLSQP')

        if not res['message'] == 'Optimization terminated successfully.':
            raise ArithmeticError('Optimization convergence may have failed!')

        return res.x











