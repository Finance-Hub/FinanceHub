from pandas.tseries.holiday import Holiday, next_monday_or_tuesday, \
    sunday_to_monday, MO
from pandas.tseries.offsets import DateOffset


NewYearsDay = Holiday('New Year´s Day', month=1, day=1,
                      observance=sunday_to_monday)

UKEarlyMayBank = Holiday('Early May Bank Holiday', month=5, day=1,
                         offset=DateOffset(weekday=MO(1)))

UKSpringBank = Holiday('Spring Bank Holiday', month=5, day=31,
                       offset=DateOffset(weekday=MO(-1)))

USIndependenceDay = Holiday('US Independence Day', month=7, day=4,
                            observance=sunday_to_monday)

UKLateSummerBank = Holiday('Late Summer Bank Holiday', month=8, day=31,
                           offset=DateOffset(weekday=MO(-1)))

USVeteransDay = Holiday('US Veteran´s Day', month=11, day=11,
                        observance=sunday_to_monday)

Christmas = Holiday('Christmas', month=12, day=25, observance=sunday_to_monday)

BoxingDay = Holiday('BoxingDay', month=12, day=26,
                    observance=next_monday_or_tuesday)
