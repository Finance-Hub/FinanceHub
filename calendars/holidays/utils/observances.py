from pandas.tseries.offsets import DateOffset
from pandas.tseries.holiday import MO


def closest_next_monday(dt):
    """Observance for next_monday"""
    return dt + DateOffset(weekday=MO(1))


def closest_previous_monday(dt):
    """Observance for previous Monday"""
    return dt + DateOffset(weekday=MO(-1))
