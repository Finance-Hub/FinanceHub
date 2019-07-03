from datetime import date
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, \
    GoodFriday, EasterMonday, nearest_workday, next_monday_or_tuesday
from calendars.holidays.utils import closest_previous_monday, \
    closest_next_monday, Y_END, Y_INI


class LiborAllTenorsAndCurrencies(AbstractHolidayCalendar):
    """Applicable to all tenors and currencies according to ICE"""

    def __init__(self):
        rules = [
            Holiday('NewYearsDay', month=1, day=1, observance=nearest_workday),
            GoodFriday,
            EasterMonday,
            Holiday('EarlyMayBankHoliday', month=5, day=1,
                    observance=closest_next_monday),
            Holiday('SpringBankHoliday', month=5, day=31,
                    observance=closest_previous_monday),
            Holiday('SummerBankHoliday', month=8, day=31,
                    observance=closest_previous_monday),
            Holiday('Christmas', month=12, day=25, observance=nearest_workday),
            Holiday('BoxingDay', month=12, day=26,
                    observance=next_monday_or_tuesday)
        ]
        super(LiborAllTenorsAndCurrencies, self).__init__(
            name='libor_all_tenors_currencies', rules=rules)

    def cdr_libor_base(self):
        """Return calendar for fixed period"""
        h = self.holidays(date(Y_INI - 1, 12, 31), date(Y_END, 12, 31))
        return list(h.date)

    def cdr_libor_usd(self):
        return self.cdr_libor_base()

    def cdr_libor_eur(self):
        return self.cdr_libor_base()

    def cdr_libor_gbp(self):
        return self.cdr_libor_base()

    def cdr_libor_gbp_on(self):
        return self.cdr_libor_base()

    def cdr_libor_chf(self):
        return self.cdr_libor_base()

    def cdr_libor_chf_on(self):
        return self.cdr_libor_base()

    def cdr_libor_jpy(self):
        return self.cdr_libor_base()

    def cdr_libor_jpy_on(self):
        return self.cdr_libor_base()
