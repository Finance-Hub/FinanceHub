import os
import pandas as pd
import matplotlib.pyplot as plt
from bloomberg import BBG
import numpy as np
from dateutil.relativedelta import relativedelta
from scipy import interpolate

bloomberg_semi_annual_swap_tickers = ['USSW1 Curncy', 'USSW2 Curncy', 'USSW3 Curncy',
                                      'USSW4 Curncy', 'USSW5 Curncy', 'USSW6 Curncy',
                                      'USSW7 Curncy', 'USSW8 Curncy', 'USSW9 Curncy',
                                      'USSW10 Curncy', 'USSW15 Curncy', 'USSW20 Curncy',
                                      'USSW25 Curncy', 'USSW30 Curncy']

bloomberg_1M_fwd_starting_tickers = ['USFS0A1 Curncy', 'USFS0A2 Curncy', 'USFS0A3 Curncy',
                                     'USFS0A4 Curncy', 'USFS0A5 Curncy', 'USFS0A6 Curncy',
                                     'USFS0A7 Curncy', 'USFS0A8 Curncy', 'USFS0A9 Curncy',
                                     'USFS0A10 Curncy', 'USFS0A15 Curncy', 'USFS0A20 Curncy',
                                     'USFS0A25 Curncy', 'USFS0A30 Curncy']


def get_interpolated_rate(x, curve):
    tck = interpolate.splrep(curve.index, curve.values)
    if x > min(curve.index):
        return float(interpolate.splev(x,tck))
    else:
        return curve[min(curve.index)]


start_date = pd.to_datetime('2003-01-02').date()
end_date = pd.to_datetime('today').date()

bbg = BBG()

raw_swap_curves = bbg.fetch_series(securities=bloomberg_semi_annual_swap_tickers,
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)
raw_swap_curves.columns = [int(x.replace('USSW','').replace(' Curncy','')) for x in list(raw_swap_curves.columns)]
raw_swap_curves = raw_swap_curves[sorted(raw_swap_curves.columns)]

fwd_start_swaps = bbg.fetch_series(securities=bloomberg_1M_fwd_starting_tickers,
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)

fwd_start_swaps.columns = [int(x.replace('USFS0A', '').replace(' Curncy', '')) for x in list(fwd_start_swaps.columns)]
fwd_start_swaps = fwd_start_swaps[sorted(fwd_start_swaps.columns)]

calendar = [x for x in raw_swap_curves.index if x in fwd_start_swaps.index]
raw_swap_curves = raw_swap_curves.loc[calendar]
fwd_start_swaps = fwd_start_swaps.loc[calendar]

notional = 100
tracker_tenor = 10
pay_freq = 2

fwd_swap_rate = fwd_start_swaps.loc[start_date,tracker_tenor]/100
ref_swap_rate_d_minus_1 = fwd_swap_rate

fwd_swap_maturity = start_date + relativedelta(months=1 + tracker_tenor*12)
roll_date = start_date + relativedelta(months=1) #TODO: this step needs to satisfy swap 30I/360 daycount standard

tracker_index = pd.Series(index=raw_swap_curves.index)
tracker_index.iloc[0] = notional

for d in tracker_index.index[1:]:
    current_fwd_swap_rate = fwd_start_swaps.loc[d,tracker_tenor]/100
    if np.isnan(current_fwd_swap_rate):
        current_fwd_swap_rate = get_interpolated_rate(tracker_tenor, fwd_start_swaps.loc[d, :].dropna() / 100)

    current_spot_swap_rate = raw_swap_curves.loc[d, tracker_tenor] / 100
    if np.isnan(current_spot_swap_rate):
        current_spot_swap_rate = get_interpolated_rate(tracker_tenor, raw_swap_curves.loc[d, :].dropna() / 100)

    # TODO: this needs to satisfy swap 30I/360 daycount standard
    current_fwd_swap_maturity = d + relativedelta(months=1 + tracker_tenor*12)
    current_spot_swap_maturity = d + relativedelta(months=tracker_tenor * 12)

    if d >= roll_date:
        w = 1
    else:
        # TODO: this needs to satisfy swap 30I/360 daycount standard
        w = (current_fwd_swap_maturity - fwd_swap_maturity).days / (current_fwd_swap_maturity - current_spot_swap_maturity).days

    ref_swap_rate = w*current_spot_swap_rate+(1-w)*current_fwd_swap_rate

    #This is the present value of a basis point using the interpolated forward swap rate as an internal rate of return
    pv01 = np.sum([(1/pay_freq)*((1+ref_swap_rate/pay_freq)**(-i)) for i in range(1,tracker_tenor*pay_freq+1)])

    if np.isnan((ref_swap_rate_d_minus_1 - ref_swap_rate)*pv01):
        ret = 0
    else:
        ret = (ref_swap_rate_d_minus_1 - ref_swap_rate)*pv01

    tracker_index[d] = tracker_index[:d].iloc[-2] *(1+ret)
    ref_swap_rate_d_minus_1 = ref_swap_rate

    if d >= roll_date:
        fwd_swap_rate = fwd_start_swaps.loc[d, tracker_tenor] / 100
        ref_swap_rate_d_minus_1 = fwd_swap_rate

        fwd_swap_maturity = d + relativedelta(months=1 + tracker_tenor * 12)
        roll_date = d + relativedelta(months=1)  # TODO: this step needs to satisfy swap 30I/360 daycount standard
        swap_rate_d_minus_1 = raw_swap_curves.loc[d,tracker_tenor]/100
        if np.isnan(swap_rate_d_minus_1):
            ref_swap_rate_d_minus_1 = get_interpolated_rate(tracker_tenor, raw_swap_curves.loc[d, :].dropna() / 100)

tracker_index.plot()
plt.show()

file_name = 'fwd_swap_tracker' + str(tracker_tenor) + 'Y.csv'
tracker_index.to_frame('backtest').to_csv(os.path.join(os.getcwd(),file_name))