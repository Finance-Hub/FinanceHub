import numpy as np
import pandas as pd

from calendars import DayCounts


class RateUtils:

    accrual_methods = ['BUS', 'ACT']

    def __init__(self, dc='BUS/252', calendar='anbima'):
        self.dc = DayCounts(dc, calendar=calendar)
        self.accrual_methods_map = {
            'BUS': self.__accrual_bus,
            'ACT': self.__accrual_act
        }

    @staticmethod
    def __accrual(rates):
        return (1 + rates).cumprod()

    def __accrual_act(self, rates, dates):
        n_days = [self.dc.days(t0, t1) for t0, t1 in zip(dates[1:], dates[:-1])]
        accrual = n_days * (rates/100)/365
        return self.__accrual(accrual)

    def __accrual_bus(self, rates, dates):
        return ((1 + rates/100)**(1/252)).cumprod()

    def accrual(self, rates: pd.Series, dates: pd.Series, method: str):
        try:
            return self.accrual_methods_map[method](rates, dates)
        except KeyError:
            print(f'Accrual method: {method} is not supported! Supported values: {RateUtils.accrual_methods}')
            raise


if __name__ == "__main__":
    cdi = pd.read_excel('../../datasets/data/CDI.xlsx')
    # reverse CDI
    cdi = cdi[::-1].reset_index()
    utils = RateUtils()

    acc = utils.accrual(cdi['CDI (taxa)'], cdi['Date'], 'BUS')
    print(acc)
