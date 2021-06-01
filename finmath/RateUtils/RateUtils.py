import numpy as np
import pandas as pd

from calendars import DayCounts


class RateUtils:

    accrual_methods = ['BUS/252', 'ACT/360', 'ACT/365']

    def __init__(self, calendar='anbima'):
        self.currency_map = {
            'BRL': {
                'method': self.__bus_252,
                'shift': 0,
            },
            'USD': {
                'method': self.__act_360,
                'shift': 1,
            },
            'CHF': {
                'method': self.__act_360,
                'shift': -1,
            },
            'EUR': {
                'method': self.__act_360,
                'shift': 0,
            },
            'GBP': {
                'method': self.__act_365,
                'shift': 0,
            },
            'JPY': {
                'method': self.__act_365,
                'shift': 1,
            },
        }
        self.calendar = calendar
        self.accrual_methods_map = {
            'BUS/252': self.__bus_252,
            'ACT/360': self.__act_360,
            'ACT/365': self.__act_365
        }

    def __act_360(self, rates, dates, shift):
        dc = DayCounts(dc='ACT/360', calendar=self.calendar)
        rates = rates.shift(shift)
        n_days = [dc.days(t0, t1) for t0, t1 in zip(dates[1:], dates[:-1])]
        accrual = n_days * (rates/100)/360
        return (1 + accrual).cumprod()

    def __act_365(self, rates, dates, shift):
        dc = DayCounts(dc='ACT/365', calendar=self.calendar)
        rates = rates.shift(shift)
        n_days = [dc.days(t0, t1) for t0, t1 in zip(dates[1:], dates[:-1])]
        accrual = n_days * (rates/100)/365
        return (1 + accrual).cumprod()

    def __bus_252(self, rates, *_):
        return ((1 + rates/100)**(1/252)).cumprod()

    def currency_accrual(self, rates: pd.Series, dates: pd.Series, currency: str):
        try:
            curr = self.currency_map[currency]
            return curr['method'](rates, dates, curr['shift'])
        except KeyError:
            print(f'Currency: {currency} is not supported! Supported values: {self.currency_map.keys()}')
            raise


if __name__ == "__main__":
    cdi = pd.read_excel('../../datasets/data/CDI.xlsx')
    # reverse CDI
    cdi = cdi[::-1].reset_index()
    utils = RateUtils()

    acc = utils.currency_accrual(cdi['CDI (taxa)'], cdi['Date'], 'BRL')
    print(acc)
