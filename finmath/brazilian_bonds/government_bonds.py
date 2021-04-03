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


def truncate(number, decimals=0):
    """Returns a value truncated to a specific number of decimal places"""
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return np.trunc(number)
    factor = 10.0 ** decimals
    return np.trunc(number * factor) / factor


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
        self.macaulay = self.ytm
        self.mod_duration = self.macaulay / (1. + self.rate)
        self.dv01 = (self.mod_duration / 100.) * self.price
        self.convexity = self.ytm * (1. + self.ytm) / (1. + self.rate) ** 2

    def price_from_rate(self,
                        principal: Optional[float] = None,
                        rate: Optional[float] = None,
                        ytm: Optional[float] = None,
                        truncate_price: bool = True):

        principal = self.principal if principal is None else principal
        rate = self.rate if rate is None else rate
        ytm = self.ytm if ytm is None else ytm
        # Adjusting according the Anbima specifications
        pu = 10*np.round(100/((1 + rate)**ytm), 10)
        if truncate_price:
            pu = truncate(pu, 6)

        return principal/1000 * pu

    def rate_from_price(self,
                        principal: Optional[float] = None,
                        price: Optional[float] = None,
                        ytm: Optional[float] = None):

        principal = self.principal if principal is None else principal
        price = self.price if price is None else price
        ytm = self.ytm if ytm is None else ytm
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
        self.principal = principal

        interest = ((1. + coupon_rate) ** (1. / 2.) - 1.) * self.principal
        cash_flows = pd.Series(index=self.payment_dates(),
                               data=interest).sort_index()
        cash_flows.iloc[-1] += self.principal

        self.cash_flows = cash_flows

        if rate is not None and price is None:
            self.rate = float(rate)
            self.price = self.price_from_rate(principal=self.principal, rate=self.rate)
        elif rate is None and price is not None:
            self.price = float(price)
            self.rate = self.rate_from_price(price=self.price)

        else:
            pt = self.price_from_rate(principal=self.principal, rate=rate)
            if np.abs(pt - float(price)) / self.principal > 0.1:
                msg = 'Given price and rate are incompatible!'
                warnings.warn(msg)
            self.rate = rate
            self.price = price

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

    def price_from_rate(self,
                        principal: Optional[float] = None,
                        rate: Optional[float] = None,
                        truncate_price: bool = True) -> float:
        pv = 0.
        principal = self.principal if principal is None else principal
        rate = self.rate if rate is None else rate
        for d, p in self.cash_flows.items():
            # Adjusting according the Anbima specifications
            p = np.round(100 * p / principal, 6)
            pv += LTN(d, ref_date=self.ref_date, price=p).price_from_rate(p, rate, None, False)

        if truncate_price:
            pv = truncate(10*pv, 6)
        # Adjusting back according to the intended principal
        return pv * principal / 1000

    def rate_from_price(self,
                        price: Optional[float] = None):

        price = self.price if price is None else price
        theor_p = lambda x: sum([
            LTN(d, ref_date=self.ref_date, price=p).price_from_rate(p, x, None, False)
            for d, p in self.cash_flows.items()
        ])
        error = lambda x: (price - float(theor_p(x)))

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
                 principal: float = 1e6,
                 coupon_rate: float = 0.06,
                 vna: Optional[float] = None,
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

        if rate is not None:
            msg_2 = 'Parameters price and vna cannot be both None!'
            assert price is not None or vna is not None, msg_2

        if price is not None:
            msg_3 = 'Parameters rate and vna cannot be both None!'
            assert rate is not None or vna is not None, msg_3

        self.expiry = pd.to_datetime(expiry).date()
        self.ref_date = pd.to_datetime(ref_date).date()
        self.principal = principal
        self.vna = vna

        interest = ((1. + coupon_rate) ** (1. / 2.) - 1.) * self.principal
        cash_flows = pd.Series(index=self.payment_dates(),
                               data=interest).sort_index()
        cash_flows.iloc[-1] += self.principal

        self.cash_flows = cash_flows

        if price is not None and rate is not None:
            self.price = float(price)
            self.rate = float(rate)
            base_price = self.price_from_rate(principal=self.principal, rate=self.rate, vna=1000)
            self.vna = np.round(self.price / base_price * 1000, 6)
        if rate is not None and price is None and vna is not None:
            self.rate = float(rate)
            self.price = self.price_from_rate(principal=self.principal, rate=self.rate, vna=self.vna)
        elif rate is None and price is not None and vna is not None:
            self.price = float(price)
            self.rate = self.rate_from_price(price=self.price, vna=self.vna)

        else:
            pt = self.price_from_rate(principal=self.principal, rate=rate)
            if np.abs(pt - float(price)) / self.principal > 0.1:
                msg = 'Given price and rate are incompatible!'
                warnings.warn(msg)
            self.rate = rate
            self.price = price

        self.mod_duration, self.convexity = self.calculate_risk
        self.macaulay = self.mod_duration * (1. + self.rate)
        self.dv01 = (self.mod_duration / 100.) * self.price

    def payment_dates(self):

        payd = [dc.following(self.expiry)]
        d = dc.workday(dc.eom(dc.following(self.expiry), offset=-7) + pd.DateOffset(days=14), 1)
        while d > dc.following(self.ref_date):
            payd += [d]
            d = dc.workday(dc.eom(d, offset=-7)+pd.DateOffset(days=14), 1)

        return sorted(payd)

    def price_from_rate(self,
                        principal: Optional[float] = None,
                        rate: Optional[float] = None,
                        vna: Optional[float] = None,
                        truncate_price: bool = True) -> float:
        pv = 0.
        principal = self.principal if principal is None else principal
        rate = self.rate if rate is None else rate
        vna = self.vna if vna is None else vna

        for d, p in self.cash_flows.items():
            # Adjusting according the Anbima specifications
            p = np.round(100 * p / principal, 6)
            pv += LTN(d, ref_date=self.ref_date, price=p).price_from_rate(p, rate, None, False)

        pv = truncate(pv, 4) * np.round(vna, 6) / 100
        if truncate_price:
            pv = truncate(pv, 6)
        # Adjusting back according to the intended principal
        return pv * principal / 1000

    def rate_from_price(self,
                        price: Optional[float] = None,
                        vna: Optional[float] = None):

        price = self.price if price is None else price
        vna = self.vna if vna is None else vna
        price /= vna
        price *= self.principal

        theor_p = lambda x: sum([
            LTN(d, ref_date=self.ref_date, price=p).price_from_rate(p, x, None, False)
            for d, p in self.cash_flows.items()
        ])
        error = lambda x: (price - float(theor_p(x)))

        return optimize.brentq(error, -0.99, 1.)

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