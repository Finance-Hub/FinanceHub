"""
Author: Gustavo Soares
"""
import warnings
from typing import Optional
import pandas as pd
import numpy as np
from calendars import DayCounts
from calendars.custom_date_types import Date, TODAY
from scipy import optimize

dc = DayCounts('bus/252', calendar='cdr_anbima')


class LTN(object):

    def __init__(self,
                 expiry: Date,
                 rate: Optional[float] = None,
                 price: Optional[float] = None,
                 principal: float = 1e6,
                 ref_date: Date = TODAY):
        """
        Class constructor.
        This is a zero coupon Brazilian government bond
        :param expiry: bond expiry date
        :param rate: bond yield
        :param price: bond price
        :param principal: bond principal
        :param ref_date: reference date for price or rate calculation
        """

        msg = 'Parameters rate and price cannot be both None!'
        assert rate is not None or price is not None, msg

        self.principal = float(principal)
        self.ytm = dc.tf(ref_date, expiry)
        self.expiry = pd.to_datetime(expiry).date()

        if rate is not None and price is None:
            self.rate = float(rate)
            self.price = self.price_from_rate(principal, rate, self.ytm)
        elif rate is None and price is not None:
            self.price = float(price)
            self.rate = self.rate_from_price(principal, price, self.ytm)
        else:
            pt = self.price_from_rate(principal, rate, self.ytm)
            if np.abs(pt - float(price)) / principal > 0.1:
                msg = 'Given price and rate are incompatible!'
                warnings.warn(msg)
            self.rate = rate
            self.price = price

        self.ref_date = pd.to_datetime(ref_date).date()
        self.cash_flows = pd.Series(index=[dc.following(self.ref_date),
                                           dc.following(self.expiry)],
                                    data=[-self.price, self.principal])

    @staticmethod
    def price_from_rate(principal: float = 1e6,
                        rate: Optional[float] = None,
                        ytm: Optional[float] = None):
        return principal / (1. + rate) ** ytm

    @staticmethod
    def rate_from_price(principal: float = 1e6,
                        price: Optional[float] = None,
                        ytm: Optional[float] = None):
        return (principal / price) ** (1. / ytm) - 1.


class NTNF(object):

    def __init__(self,
                 expiry: Date,
                 rate: Optional[float] = None,
                 price: Optional[float] = None,
                 principal: float = 1e6,
                 coupon_rate: float = 0.1,
                 ref_date: Date = TODAY):
        """
        Class constructor.
        This is a Brazilian government bond that pays coupons every six months
        :param expiry: bond expiry date
        :param rate: bond yield
        :param price: bond price
        :param principal: bond principal
        :param coupon_rate: bond coupon rate
        :param ref_date: reference date for price or rate calculation
        """

        msg = 'Parameters rate and price cannot be both None!'
        assert rate is not None or price is not None, msg

        self.expiry = pd.to_datetime(expiry).date()
        self.ref_date = pd.to_datetime(ref_date).date()

        interest = ((1. + coupon_rate) ** (1. / 2.) - 1.) * principal
        cash_flows = pd.Series(index=self.payment_dates(),
                               data=interest).sort_index()
        cash_flows.iloc[-1] += principal

        self.cash_flows = cash_flows

        if rate is not None and price is None:
            self.rate: float = float(rate)
            self.price = self.price_from_rate()
        elif rate is None and price is not None:
            self.price = float(price)
            self.rate = self.rate_from_price()

        else:
            pt = self.price_from_rate()
            if np.abs(pt - float(price)) / principal > 0.1:
                msg = 'Given price and rate are incompatible!'
                warnings.warn(msg)
            self.rate = rate
            self.price = price

    def payment_dates(self):

        payd = [dc.following(self.expiry)]
        d = dc.workday(dc.eom(dc.following(self.expiry), offset=-7), 1)
        while d > dc.following(self.ref_date):
            payd += [d]
            d = dc.workday(dc.eom(d, offset=-7), 1)

        return sorted(payd)

    def price_from_rate(self) -> float:
        pv = 0.
        for d, p in self.cash_flows.items():
            cf = LTN(d, rate=self.rate, principal=p,
                     ref_date=self.ref_date)
            pv += cf.price
        return float(pv)

    def rate_from_price(self):
        p = lambda x: sum([LTN(d, rate=x, principal=p,
                               ref_date=self.ref_date).price
                           for d, p in self.cash_flows.items()])
        error = lambda x: (self.price - float(p(x)))

        return optimize.brentq(error, 0., 1.)
