import os
import pandas as pd
import matplotlib.pyplot as plt
from fhdataapi import BBG
import numpy as np
from dateutil.relativedelta import relativedelta
from scipy import interpolate

def get_interpolated_rate(x,curve):
    tck = interpolate.splrep(curve.index, curve.values)
    if x> min(curve.index):
        return float(interpolate.splev(x,tck))
    else:
        return curve[min(curve.index)]

def get_discount_factor(r,T):
    return 1 / ((1 + r) ** T)

def get_swap_cash_flow_fixed_leg(ref_rate, ref_date, tenor, notional=100000000):
    cash_flows = pd.Series()
    d = ref_date + relativedelta(months=6)
    c = notional * ref_rate / 2
    cash_flows[d] = c
    for i in range(1, tenor * 2):
        d = d + relativedelta(months=6)
        cash_flows[d] = c

    cash_flows.iloc[-1] = cash_flows.iloc[-1] + notional
    return cash_flows

def get_swap_cash_flows_floating_leg(zero_curve, ref_date, cash_flow, notional=100000000):
    cf = pd.Series(0, index=cash_flow.loc[ref_date:].index)  # not correct
    T1 = 0
    for i in range(0, len(cf.index)):
        T2 = T1 + 0.5
        r1 = get_interpolated_rate(T1, zero_curve)
        r2 = get_interpolated_rate(T2, zero_curve)
        fwd_rate = (((1 + r2) ** T2) / ((1 + r1) ** T1)) ** ((1.0 / (T2 - T1))) - 1
        cf.iloc[i] = notional * fwd_rate / 2
        T1 = T2
    cf.iloc[-1] = cf.iloc[-1] + notional

    return cf

def get_cash_flow_pv_with_zero_curve(ref_date, cash_flow, zero_curve):
    all_data = pd.DataFrame(0, index=cash_flow.index, columns=['cf', 'df', 'T', 'r', 'dcf'])

    cf = cash_flow.loc[ref_date:].copy()
    T1 = (cf.index[0] - ref_date).days / 360.0  # Changed
    r1 = get_interpolated_rate(T1, zero_curve)
    df1 = get_discount_factor(r1, T1)
    df = [df1]
    pv = cf.iloc[0] * df1

    all_data.loc[cf.index[0], 'cf'] = cf.iloc[0]
    all_data.loc[cf.index[0], 'df'] = df1
    all_data.loc[cf.index[0], 'T'] = T1
    all_data.loc[cf.index[0], 'r'] = r1
    all_data.loc[cf.index[0], 'dcf'] = pv
    T2 = T1  # New
    for i in range(1, len(cf.index)):
        T2 = T2 + 0.5  # Changed
        r2 = get_interpolated_rate(T2, zero_curve)
        df2 = get_discount_factor(r2, T2)
        df.append(df2)
        cf2 = cash_flow.iloc[i]  # Broken out calc
        dcf = cf2 * df2  # Broken out calc
        pv += dcf  # Broken out calc

        all_data.loc[cf.index[i], 'cf'] = cf2  # New
        all_data.loc[cf.index[i], 'df'] = df2  # New
        all_data.loc[cf.index[i], 'T'] = T2  # New
        all_data.loc[cf.index[i], 'r'] = r2  # New
        all_data.loc[cf.index[i], 'dcf'] = dcf  # New
    return pv, df, all_data  # Changed

def get_cash_flow_pv_with_swap_rate(ref_rate, ref_date, cash_flow):
    cf = cash_flow.loc[ref_date:].copy()
    T1 = (cf.index[0] - ref_date).days / 360.0  # Changed
    df1 = get_discount_factor(ref_rate, T1)
    df = [df1]
    pv = cf.iloc[0] * df1
    for i in range(1, len(cf.index)):
        T2 = T1 + 0.5
        df2 = get_discount_factor(ref_rate, T2)
        df.append(df2)
        pv += cash_flow.iloc[i] * df2
    return pv, df

# get the zero coupon curve to calculate discount factors
bloomberg_semi_annual_swap_tickers = [
    'USSW1 Curncy',
    'USSW2 Curncy',
    'USSW3 Curncy',
    'USSW4 Curncy',
    'USSW5 Curncy',
    'USSW6 Curncy',
    'USSW7 Curncy',
    'USSW8 Curncy',
    'USSW9 Curncy',
    'USSW10 Curncy',
    'USSW15 Curncy',
    'USSW20 Curncy',
    'USSW25 Curncy',
    'USSW30 Curncy'
]

bloomberg_zero_coupon_tickers = [
'S0023Z 1Y BLC2 Curncy',
'S0023Z 18M BLC2 Curncy',
'S0023Z 2Y BLC2 Curncy',
'S0023Z 30M BLC2 Curncy',
'S0023Z 3Y BLC2 Curncy',
'S0023Z 42M BLC2 Curncy',
'S0023Z 4Y BLC2 Curncy',
'S0023Z 5Y BLC2 Curncy',
'S0023Z 6Y BLC2 Curncy',
'S0023Z 7Y BLC2 Curncy',
'S0023Z 8Y BLC2 Curncy',
'S0023Z 9Y BLC2 Curncy',
'S0023Z 10Y BLC2 Curncy',
'S0023Z 11Y BLC2 Curncy',
'S0023Z 12Y BLC2 Curncy',
'S0023Z 13Y BLC2 Curncy',
'S0023Z 14Y BLC2 Curncy',
'S0023Z 15Y BLC2 Curncy',
'S0023Z 16Y BLC2 Curncy',
'S0023Z 17Y BLC2 Curncy',
'S0023Z 18Y BLC2 Curncy',
'S0023Z 19Y BLC2 Curncy',
'S0023Z 20Y BLC2 Curncy',
'S0023Z 21Y BLC2 Curncy',
'S0023Z 22Y BLC2 Curncy',
'S0023Z 23Y BLC2 Curncy',
'S0023Z 24Y BLC2 Curncy',
'S0023Z 25Y BLC2 Curncy',
'S0023Z 26Y BLC2 Curncy',
'S0023Z 27Y BLC2 Curncy',
'S0023Z 28Y BLC2 Curncy',
'S0023Z 29Y BLC2 Curncy',
'S0023Z 30Y BLC2 Curncy',
]

start_date = pd.to_datetime('2003-01-02').date()
end_date = pd.to_datetime('today').date()

bbg = BBG()

raw_swap_curves = bbg.fetch_series(securities=bloomberg_semi_annual_swap_tickers,
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)
raw_swap_curves.columns = [int(x.replace('USSW','').replace(' Curncy','')) for x in list(raw_swap_curves.columns)]
raw_swap_curves = raw_swap_curves[sorted(raw_swap_curves.columns)]

zero_coupon_curve = bbg.fetch_series(securities=bloomberg_zero_coupon_tickers,
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)

zero_coupon_curve.columns = [x.replace('S0023Z ','').replace(' BLC2 Curncy','') for x in list(zero_coupon_curve.columns)]
zero_coupon_curve.columns = [(float(x.replace('Y',''))*12 if x.find('Y')>-1 else float(x.replace('M','')))/12
                                                                    for x in list(zero_coupon_curve.columns)]
zero_coupon_curve = zero_coupon_curve[sorted(zero_coupon_curve.columns)]

notional = 100
tracker_tenor = 10
roll_months = 1
tracker_index = pd.Series(index=raw_swap_curves.index)
tracker_index.iloc[0] = notional


next_roll_date = start_date + relativedelta(months=roll_months)
swap_rate_d_minus_1 = raw_swap_curves.loc[start_date,tracker_tenor]/100
zc_curve = zero_coupon_curve.loc[start_date,:]/100
fixed_rate_cash_flow = get_swap_cash_flow_fixed_leg(swap_rate_d_minus_1,start_date,tracker_tenor,notional=notional)
float_rate_cash_flow = get_swap_cash_flows_floating_leg(zc_curve,start_date,fixed_rate_cash_flow,notional=notional)
pv_float, df1, all_data1 = get_cash_flow_pv_with_zero_curve(start_date,float_rate_cash_flow,zc_curve)
pv_fixed, df2, all_data2 = get_cash_flow_pv_with_zero_curve(start_date,fixed_rate_cash_flow,zc_curve)
pv_swap_d_minus_1 = pv_fixed - pv_float


for d in tracker_index.index[1:]:
    zc_curve = zero_coupon_curve.loc[d, :] / 100
    float_rate_cash_flow = get_swap_cash_flows_floating_leg(zc_curve, d, fixed_rate_cash_flow,notional=notional)
    pv_float, df1, all_data1 = get_cash_flow_pv_with_zero_curve(d, float_rate_cash_flow, zc_curve)
    pv_fixed, df2, all_data2 = get_cash_flow_pv_with_zero_curve(d, fixed_rate_cash_flow, zc_curve)
    pv_swap_d = pv_fixed - pv_float
    tracker_index[d] = tracker_index[:d].iloc[-2] + (pv_swap_d - pv_swap_d_minus_1)
    pv_swap_d_minus_1 = pv_swap_d
    print('%s : %s' % (d.strftime('%d-%b-%y'), tracker_index[d]))

    if d >= next_roll_date:
        print('rolling swap')
        next_roll_date = d + relativedelta(months=roll_months)
        notional = tracker_index[d]
        swap_rate_d_minus_1 = raw_swap_curves.loc[d,tracker_tenor]/100
        if np.isnan(swap_rate_d_minus_1):
            swap_rate_d_minus_1 = get_interpolated_rate(tracker_tenor, raw_swap_curves.loc[d, :].dropna() / 100)

        fixed_rate_cash_flow = get_swap_cash_flow_fixed_leg(swap_rate_d_minus_1,d,tracker_tenor,notional=notional)
        float_rate_cash_flow = get_swap_cash_flows_floating_leg(zc_curve,d,fixed_rate_cash_flow,notional=notional)
        pv_float, df1, all_data1 = get_cash_flow_pv_with_zero_curve(d,float_rate_cash_flow,zc_curve)
        pv_fixed, df2, all_data2 = get_cash_flow_pv_with_zero_curve(d,fixed_rate_cash_flow,zc_curve)
        pv_swap_d_minus_1 = pv_fixed - pv_float

tracker_index.plot()
plt.show()

file_name = 'tracker' + str(tracker_tenor) + 'Y.csv'
tracker_index.to_frame('backtest').to_csv(os.path.join(os.getcwd(),file_name))
