from pandas.tseries.holiday import AbstractHolidayCalendar
from .constants import Y_END, Y_INI
from datetime import date


class AbstractBase(AbstractHolidayCalendar):
    _config = None

    def __init__(self, name):
        super(AbstractBase, self).__init__(name=name, rules=self._config)

    def _base_caller(self):
        """Base caller generates list of holiday dates using inherited
        method. The method holidays returns a DatetimeIndex object,
        however for backward compatibility we `cast` this into a list of
        datetime.date"""
        h = self.holidays(date(Y_INI - 1, 12, 31), date(Y_END, 12, 31))
        return list(h.date)
