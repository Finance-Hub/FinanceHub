
"""
@author: Vitor Eller
"""

import pandas as pd

from datetime import datetime


class AnbimaHolidays(object):

    path = 'brazilian_holidays_anbima.xlsx'

    def __init__(self):

        dates = pd.read_excel(self.path)
        self.holidays = self._set_holidays(dates)

    def get_holidays(self):

        return self.holidays

    def check_date(self, date):

        if type(date) is datetime.day:
            y = date.year
            m = date.month
            d = date.day
            date = datetime.datetime(y, m, d)
        elif type(date) is not datetime.datetime:
            raise TypeError('Please input a Datetime object.')

        if date in self.holidays:
            return True
        return False

    @staticmethod
    def _set_holidays(dates):

        holidays = set()
        for holiday in dates:
            y = holiday.year
            m = holiday.month
            d = holiday.day
            holidays.add(datetime.datetime(y, m, d))

        return holidays
