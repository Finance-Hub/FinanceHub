from calendars.holidays.utils import AbstractBase
from pandas.tseries.holiday import USMartinLutherKingJr, USPresidentsDay, \
    GoodFriday, USMemorialDay, USLaborDay, USThanksgivingDay
from calendars.holidays.utils import NewYearsDay, USIndependenceDay, Christmas


class USTradingCalendar(AbstractBase):
    """United States Trading Calendar"""
    _config = [NewYearsDay,
               USMartinLutherKingJr,
               USPresidentsDay,
               GoodFriday,
               USMemorialDay,
               USIndependenceDay,
               USLaborDay,
               USThanksgivingDay,
               Christmas]

    def __init__(self):
        super(USTradingCalendar, self).__init__(name='us_trading')

    def cdr_us_trading(self):
        """Return calendar for fixed period"""
        return self._base_caller()
