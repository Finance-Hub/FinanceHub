
"""
@author: Vitor Eller (@VFermat)
"""

import pandas as pd

from datetime import datetime


class AnbimaHolidays(object):

    path = 'brazilian_holidays_anbima.xlsx'

    def __init__(self):
        """This class is responsible for informing the user which dates are considered
        holidays for ANBIMA in Brazil.
        """

        dates = pd.read_excel(self.path)
        self.holidays = self._set_holidays(dates)

    def get_holidays(self):
        """This function returns a set containing ANBIMA's holidays from 2001 to 2070.
        """

        return self.holidays

    def check_date(self, date):
        """This function checks if a specific date is an ANBIMA holiday or not
        
        Arguments:
            date : datetime object
                A Datetime Object which represents the date the user wants to check. 
        """

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
