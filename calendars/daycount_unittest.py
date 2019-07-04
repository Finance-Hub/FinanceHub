from calendars import DayCounts
import pandas as pd


# Case 1 - d1 and d2 are Timestamps
# d1 = pd.to_datetime('2015-01-01')
# d2 = pd.to_datetime('2019-07-07')

# Case 2 - d1 is a collection and d2 is a Timestamp
# d1 = pd.date_range('2019-01-01', '2019-12-31', freq='M')
# d2 = pd.to_datetime('2019-07-07')

# Case 3 - d1 is a Timestamp and d2 is a collection
# d1 = pd.to_datetime('2019-07-07')
# d2 = pd.date_range('2019-01-01', '2019-12-31', freq='M')

# Case 4 - d1 and d2 are collections
d1 = pd.date_range('2015-01-01', '2015-12-31', freq='M')
d2 = pd.date_range('2019-01-01', '2019-12-31', freq='M')


dc = DayCounts(dc='bus/252', calendar='anbima')

print('tf - Time Fraction')
res = dc.tf(d1, d2)
print(res, '\n')


print('days - Number of days')
res = dc.days(d1, d2)
print(res, '\n')


print('Adjust - ????')

res = dc.adjust(d1)
print(res, '\n')


print('daysnodc - Actual number of days, irrespective of daycount')
res = dc.daysnodc(d1, d2)
print(res, '\n')


print('dib - Days in base according to day count convention of the object')
res = dc.dib(d1, d2)
print(res, '\n')


print('bdy - DBusiness days in year of date(s) d')
res = dc.bdy(d1)
print(res, '\n')


print('hasleap - Check if there is a leap year in range between d1 and d2')
res = dc.hasleap(d1, d2)
print(res, '\n')


print('leapdays - Calculate number of leap days between two dates, in the interval (d1, d2]')
res = dc.leapdays(d1, d2)
print(res, '\n')


print('dy - Days in year given by date(s) d')
res = dc.dy(d1)
print(res, '\n')


print('isleap - Determine if year for input date(s) is leap (True) or not (False)')
res = dc.isleap(d1)
print(res, '\n')


print('isbus - True if date is a business day')
res = dc.isbus(d1)
print(res, '\n')


print('busdateroll - Rolls business date according to convention specified in roll')
res = dc.busdateroll(d1, roll='following')
print(res, '\n')


print('workday - Mimics the workday function in Excel')
res = dc.workday(d1, offset=1)
print(res, '\n')


print('following - Returns next business date if date is weekend or holiday')
res = dc.following(d1)
print(res, '\n')


print('modified_following - Uses next business day unless it falls on a different month - in which case uses previous')
res = dc.modified_following(d1)
print(res, '\n')


print('preceding - Find preceding business date if date is weekend or holiday')
res = dc.preceding(d1)
print(res, '\n')


print('modified_preceding - Uses previous business day unless it falls on a different month - in which case uses following')
res = dc.modified_preceding(d1)
print(res, '\n')


print('eom - Unmodified end-of-month. Returns the last date of month for the same month and year as input d')
res = dc.eom(d1)
print(res, '\n')


print('eom_preceding - Returns last date of month for the same month and year as input d, unless it is not a BUS date - in that case, returns preceding date')
res = dc.eom_preceding(d1)
print(res, '\n')


print('eom_following - Returns last date of month for the same month and year as input d, unless it is not a BUS date - in that case, returns following date')
res = dc.eom_following(d1)
print(res, '\n')


print('eoy')
res = dc.eoy(d1)
print(res, '\n')


print('eoy_preceding')
res = dc.eoy_preceding(d1)
print(res, '\n')


print('eoy_following')
res = dc.eoy_following(d1)
print(res, '\n')


print('gendates')
res = dc.gendates(d1, d2)
print(res, '\n')