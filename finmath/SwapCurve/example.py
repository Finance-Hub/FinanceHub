import pandas as pd
from finmath import SwapCurve

data = pd.read_excel('example.xlsx', index_col=0)
swap_curve = SwapCurve(data, convention='business_days', calendar='br_anbima')

# Getting rate for an specific date

date = [data.columns[45]]
day_units = 35
method = 'cubic'
rate = swap_curve.get_rate(date, [day_units], interpolate_methods=[method])[method][day_units]

print('Date: {}'.format(date))
print('Rate: {}'.format(rate))
print()

# Getting the Historic Rate for that Day Units Value

historic = swap_curve.get_historic_rates(day_units, plot=True)

print(historic)
print()

# Plotting the Surface of the curve

swap_curve.plot_3d()

# Getting the historic of a forward rate

day_units_one = 360
day_units_two = 720
method = 'flat_forward'

historic = swap_curve.get_historic_forward(day_units_one, day_units_two,
                                           plot=True, interpolate_method=method)

print(historic)
print()

# Getting the historic of the duration of a maturity

day_units = 360

historic = swap_curve.get_historic_duration(day_units, plot=True)

print(historic)
print()
