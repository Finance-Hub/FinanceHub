from .brazil import BRCalendars
from .us import USTradingCalendar
from .libor import LiborAllTenorsAndCurrencies, LiborEurON, LiborUsdON


class Holidays(object):
    STDCAL      = 'cdr_standard'
    ENGINES     = [BRCalendars(), USTradingCalendar(), LiborAllTenorsAndCurrencies(), LiborEurON(), LiborUsdON()]
    # Note that we instantiate the objects in the ENGINE variable because
    # not all calendars are accessible via static methods. In this case,
    # just passing the pointer will fail in the holidays() method

    @staticmethod
    def holidays(cdr=None):
        """Factory interface"""
        # Save original name for error message
        cn      = cdr
        cdr     = Holidays.modify_calendar_name(cdr)
        if cdr is None or cdr == Holidays.STDCAL:
            return []
        for en in Holidays.ENGINES:
            try:
                h = getattr(en, cdr)
                return h()
            except AttributeError:
                pass
        raise NotImplementedError('Calendar `%s` not found. Please implement '
                                  'it.' % cn)

    @staticmethod
    def modify_calendar_name(cdr=None):
        if cdr is None or cdr == Holidays.STDCAL or \
                cdr == Holidays.STDCAL.replace('cdr_', ''):
            return Holidays.STDCAL
        assert isinstance(cdr, str), 'Cdr must be either None or a string'
        cdr = cdr.lower()
        # Save original name for error message below
        if 'cdr_' not in cdr:
            cdr = 'cdr_' + cdr
        # Hashes are not allowed, to we deal with it here
        if cdr == 'cdr_#a':
            cdr = 'cdr_us_trading'
        return cdr
