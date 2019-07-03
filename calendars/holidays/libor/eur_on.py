from calendars.holidays.utils import AbstractBase
from pandas.tseries.holiday import GoodFriday, EasterMonday
from calendars.holidays.utils import NewYearsDay, UKEarlyMayBank, UKSpringBank,\
    UKLateSummerBank, Christmas, BoxingDay, InternationalLaborDay


class LiborEurON(AbstractBase):
    """Applicable only to the Overnight Libor EUR rate"""
    _config = [NewYearsDay,
               GoodFriday,
               EasterMonday,
               InternationalLaborDay,
               UKEarlyMayBank,
               UKSpringBank,
               UKLateSummerBank,
               Christmas,
               BoxingDay]

    def __init__(self):
        super(LiborEurON, self).__init__(name='libor_eur_on')

    def cdr_libor_eur_on(self):
        """Return calendar for fixed period"""
        return self._base_caller()
