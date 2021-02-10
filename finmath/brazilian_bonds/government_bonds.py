"""
Author: Gustavo Soares
"""
import warnings
from typing import Optional
import pandas as pd
import numpy as np
from calendars import DayCounts
from calendars.custom_date_types import Date, TODAY

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
        self.cash_flows = pd.Series(index=[self.ref_date, self.expiry],
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
