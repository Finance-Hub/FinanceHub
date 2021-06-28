"""
Author: Gustavo Soares
"""
import warnings
from typing import Optional
import pandas as pd
import numpy as np
import math as mt
from calendars import DayCounts
from calendars.custom_date_types import Date, TODAY
from scipy import optimize

dc = DayCounts('bus/252', calendar='cdr_anbima')


def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return mt.trunc(stepper * number) / stepper


class LTN(object):

    def __init__(self,
                 expiry: Date,
                 rate: Optional[float] = None,
                 price: Optional[float] = None,
                 principal: float = 1e3,
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

        self.principal = float(principal)
        self.ytm = truncate(dc.tf(ref_date, expiry), 14)
        self.expiry = pd.to_datetime(expiry).date()

        if rate is not None and price is None:
            self.rate = float(rate)
            self.price = truncate(self.price_from_rate(principal, rate, self.ytm), 6)
        elif rate is None and price is not None:
            self.price = float(price)
            self.rate = truncate(self.rate_from_price(principal, price, self.ytm), 6)
        elif rate is None and price is None:
            msg = 'Parameters rate and price cannot be both None!'
            warnings.warn(msg)
            self.price = 1
            self.rate = 1
        else:
            pt = self.price_from_rate(principal, rate, self.ytm)
            if np.abs(pt - float(price)) > 0.000001:
                msg = 'Given price and rate are incompatible!'
                warnings.warn(msg)
            self.rate = rate
            self.price = price

        self.ref_date = pd.to_datetime(ref_date).date()
        self.macaulay = self.ytm
        self.mod_duration = self.macaulay / (1. + self.rate)
        self.dv01 = (self.mod_duration / 100.) * self.price
        self.convexity = self.ytm * (1. + self.ytm) / (1. + self.rate) ** 2

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
                 principal: float = 1e3,
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

        self.expiry = pd.to_datetime(expiry).date()
        self.ref_date = pd.to_datetime(ref_date).date()
        self.principal = float(principal)

        interest = np.round(((1. + coupon_rate) ** (1. / 2.) - 1.) * 1000, 5)
        cash_flows = pd.Series(index=self.payment_dates(),
                               data=interest).sort_index()
        cash_flows.iloc[-1] += 1000

        self.cash_flows = cash_flows

        if rate is not None and price is None:
            self.rate = float(rate)
            self.price = truncate(self.price_from_rate(), 6)
        elif rate is None and price is not None:
            self.price = float(price)
            self.rate = truncate(self.rate_from_price(), 6)
        elif rate is None and price is None:
            msg = 'Parameters rate and price cannot be both None!'
            warnings.warn(msg)
            self.price = 1
            self.rate = 1
        elif rate is not None and price is not None:
            self.price = float(price)
            self.rate = float(rate)

            check = self.price_from_rate()
            if np.abs(check - float(price)) > 0.000001:
                msg = 'Given price and rate are incompatible!'
                warnings.warn(msg)

        else:
            msg = 'Something wrong has happened, please check your inputs'
            warnings.warn(msg)
            self.rate = float(rate)
            self.price = float(price)

        self.mod_duration, self.convexity = self.calculate_risk
        self.macaulay = self.mod_duration * (1. + self.rate)
        self.dv01 = (self.mod_duration / 100.) * self.price

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
            cf = np.round(p / (1. + self.rate) ** dc.tf(self.ref_date, d), 9)
            pv += cf
        return float(pv)

    def rate_from_price(self):
        theor_p = lambda x: sum(np.round(p / (1. + x) ** dc.tf(self.ref_date, d), 9)
                                for d, p in self.cash_flows.items())
        error = lambda x: (self.price - float(theor_p(x)))

        return optimize.brentq(error, 0., 1.)

    @property
    def calculate_risk(self):
        macaulay = 0.
        convexity = 0.
        for d, p in self.cash_flows.items():
            pv = p / (1. + self.rate) ** dc.tf(self.ref_date, d)
            t = dc.tf(self.ref_date, d)
            macaulay += t * pv
            convexity += t * (1 + t) * pv
        macaulay = macaulay / self.price
        mod_duration = macaulay / (1. + self.rate)
        convexity = (convexity / self.price) / (1. + self.rate) ** 2

        return mod_duration, convexity


class NTNB(object):

    def __init__(self,
                 expiry: Date,
                 rate: Optional[float] = None,
                 price: Optional[float] = None,
                 vna: Optional[float] = None,
                 principal: float = 1e6,
                 coupon_rate: float = 0.06,
                 ref_date: Date = TODAY):
        """
        Class constructor.
        This is a Brazilian government bond that pays coupons every six months
        :param expiry: bond expiry date
        :param rate: bond yield
        :param price: bond price
        :param vna: updated nominal price
        :param principal: bond principal
        :param coupon_rate: bond coupon rate
        :param ref_date: reference date for price or rate calculation
        """

        self.expiry = pd.to_datetime(expiry).date()
        self.ref_date = pd.to_datetime(ref_date).date()
        self.principal = float(principal)

        interest = np.round(((1. + coupon_rate) ** (1. / 2.) - 1.) * 100, 6)
        cash_flows = pd.Series(index=self.payment_dates(),
                               data=interest).sort_index()
        cash_flows.iloc[-1] += 100

        self.cash_flows = cash_flows

        # Returns if 2 out 3 parametres are filled:
        if rate is not None and vna is not None and price is None:
            self.rate = float(rate)
            self.vna = float(vna)
            self.price = truncate(self.price_from_rate_and_vna(), 6)
        elif rate is None and vna is not None and price is not None:
            self.price = float(price)
            self.vna = float(vna)
            self.rate = truncate(self.rate_from_price_and_vna(), 6)
        elif rate is not None and vna is None and price is not None:
            self.price = float(price)
            self.rate = float(rate)
            self.vna = round(self.vna_from_price_and_rate(), 6)

        # Errors parametres are not correctly filled:
        elif (rate is None and price is None
              or rate is None and vna is None
              or price is None and vna is None):
            msg = 'Only 2 of the parameters rate, price and vna can be None!'
            warnings.warn(msg)
            self.price = 1
            self.rate = 1
            self.vna = 1

        # Checks if the parameters are compatible:
        elif rate is not None and price is not None and vna is not None:
            self.price = float(price)
            self.rate = float(rate)
            self.vna = float(vna)

            check = self.price_from_rate_and_vna()

            if np.abs(check - float(price)) > 0.000001:
                msg = 'Given price, rate and vna are incompatible!'
                warnings.warn(msg)

        else:
            msg = 'Something wrong has happened, please check your inputs'
            warnings.warn(msg)
            self.rate = float(rate)
            self.price = float(price)
            self.vna = float(vna)

        self.mod_duration, self.convexity = self.calculate_risk
        self.macaulay = self.mod_duration * (1. + self.rate)
        self.dv01 = (self.mod_duration / 100.) * self.price

    def payment_dates(self):

        payd = [dc.following(self.expiry)]
        adjpayd = list()
        d = dc.following(self.expiry) + pd.DateOffset(months=-6)

        while d > dc.following(self.ref_date):
            payd += [d]
            d = d + pd.DateOffset(months=-6)

        for day in payd:
            if day == dc.workday((day + pd.DateOffset(days=-1)), 1):
                adjday = day
            else:
                adjday = dc.workday((day + pd.DateOffset(days=-1)), 1)
            adjpayd += [adjday]

        return sorted(adjpayd)

    def price_from_rate_and_vna(self) -> float:
        pv = 0.

        for d, p in self.cash_flows.items():
            cf = np.round(p / (1. + self.rate) ** dc.tf(self.ref_date, d), 10)
            pv += cf
        return truncate(float(pv) / 100, 6) * self.vna

    def rate_from_price_and_vna(self):
        theor_p = lambda x: sum(np.round(p / (1. + x) ** dc.tf(self.ref_date, d), 9)
                                for d, p in self.cash_flows.items())
        error = lambda x: (self.price - float(truncate(theor_p(x) / 100, 6) * self.vna))

        return optimize.brentq(error, 0., 1.)

    def vna_from_price_and_rate(self):
        pv = 0.

        for d, p in self.cash_flows.items():
            cf = np.round(p / (1. + self.rate) ** dc.tf(self.ref_date, d), 10)
            pv += cf

        return self.price / truncate(float(pv) / 100, 6)

    @property
    def calculate_risk(self):
        macaulay = 0.
        convexity = 0.
        for d, p in self.cash_flows.items():
            pv = p / (1. + self.rate) ** dc.tf(self.ref_date, d)
            t = dc.tf(self.ref_date, d)
            macaulay += t * pv
            convexity += t * (1 + t) * pv
        macaulay = macaulay / self.price
        mod_duration = macaulay / (1. + self.rate)
        convexity = (convexity / self.price) / (1. + self.rate) ** 2

        return mod_duration, convexity
