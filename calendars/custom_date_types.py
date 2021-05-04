from pandas import Timestamp
from pandas.core.tools.datetimes import DatetimeScalar
from typing import Union
from datetime import date, datetime
from numpy.core import datetime64

Date = Union[DatetimeScalar, Timestamp, date, datetime64]
TODAY = Timestamp.today().date()
