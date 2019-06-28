from calendars.holidays.utils import AbstractBase
from pandas.tseries.holiday import GoodFriday, EasterMonday, \
    USMartinLutherKingJr, USPresidentsDay, USLaborDay, USColumbusDay, \
    USThanksgivingDay
from calendars.holidays.utils import NewYearsDay, UKEarlyMayBank, UKSpringBank,\
    USIndependenceDay, UKLateSummerBank, USVeteransDay, Christmas, BoxingDay


class LiborUsdON(AbstractBase):
    """Applicable only to the overnight rate for Libor USD"""

    _config = [NewYearsDay,
               USMartinLutherKingJr,
               USPresidentsDay,
               GoodFriday,
               EasterMonday,
               UKEarlyMayBank,
               UKSpringBank,
               USIndependenceDay,
               UKLateSummerBank,
               USLaborDay,
               USColumbusDay,
               USVeteransDay,
               USThanksgivingDay,
               Christmas,
               BoxingDay]

    def __init__(self):
        super(LiborUsdON, self).__init__(name='libor_usd_on')

    def cdr_libor_usd_on(self):
        """Return calendar for fixed period"""
        return self._base_caller()
