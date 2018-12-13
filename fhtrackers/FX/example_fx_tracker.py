import numpy as np
from scipy.interpolate import interp1d
import pandas as pd
from pandas.tseries.offsets import BDay
from datetime import timedelta
import matplotlib.pyplot as plt
from fhdataapi import BBG

bbg = BBG()

# ===== User Defined Parameters =====
currency = 'EUR'  # Currency to build the tracker against the USD
n_trades = 20  # Number of trackers to smooth the changes in holdings
start_date = '2000-01-04'
end_date = '2016-12-31'

# Bloomberg tickers for the currency futures
dict_tickers = {currency + ' Curncy': 'spot',
                currency + '1W Curncy': '1w',
                currency + '1M Curncy': '1m',
                currency + '2M Curncy': '2m'}

# day until maturity
dict_dc = {'spot': 0,
           '1w': 7,
           '1m': 31,
           '2m': 62}

# grabs data from bloomberg
df_bbg = bbg.fetch_series(securities=list(dict_tickers.keys()),
                          fields='PX_LAST',
                          startdate=start_date,
                          enddate=end_date)
df_bbg = df_bbg.rename_axis(dict_tickers, axis=1)

# DataFrame to hold settlement dates
df_value_dates = pd.DataFrame(index=df_bbg.index,
                              columns=df_bbg.columns)

# DataFrame to hold the outright forward (not the basis)
df_forwards = pd.DataFrame(index=df_bbg.index,
                           columns=df_bbg.columns)

for mat in dict_dc.keys():

    # trade settles in 2 business days, so we get the settlement date +2 bus days
    df_value_dates[mat] = df_bbg.index + timedelta(days=dict_dc[mat]) + BDay(2)

    if mat == 'spot':
        df_forwards[mat] = df_bbg['spot']
    else:
        df_forwards[mat] = df_bbg['spot'] + df_bbg[mat].multiply(1/10000)

# DataFrame to hold the number of days between the spot date and the settlement date
df_daycount_dc = pd.DataFrame(index=df_bbg.index)

for mat in dict_dc.keys():
    df_daycount_dc[mat] = [(a - b).days for a, b in zip(df_value_dates[mat], df_value_dates['spot'])]

# Percentage of notional to trade each day
pct_notional = 1 / float(n_trades)

# holds necessary information for calculations
df_calc = pd.DataFrame(index=range(n_trades),
                       columns=['pnl', 'fwd mtm', 'fwd strike', 'fwd day count', 'notionals'])

# maturity of the forward being traded
days_mat_new_position = (df_value_dates['spot'] - df_value_dates['spot'].shift(n_trades)).shift(-n_trades)

# start the tracker with 100 notional
df_tracker = pd.DataFrame(index=df_bbg.index,
                          columns=['index'],
                          data=100)

for d, dm1 in zip(df_tracker.index[1:], df_tracker.index[:-1]):

    # move trades down by 1 position
    df_calc['fwd day count'] = df_calc['fwd day count'].shift(1)
    df_calc['notionals'] = df_calc['notionals'].shift(1)
    df_calc['fwd strike'] = df_calc['fwd strike'].shift(1)

    # add values for the new position
    df_calc['fwd day count'].loc[0] = days_mat_new_position[dm1].days - (df_value_dates['spot'][d] - df_value_dates['spot'][dm1]).days

    df_calc['notionals'].loc[0] = df_tracker.loc[dm1, 'index'] * pct_notional  # each of the n_trades positions has the same percentage of the notional

    df_calc['fwd strike'].loc[0] = np.interp(days_mat_new_position[dm1].days,
                                             df_daycount_dc.loc[dm1].astype(float).values,
                                             df_forwards.loc[dm1].astype(float).values)

    # mark to market the forwards that we are holding
    df_calc['fwd mtm'] = np.interp(df_calc['fwd day count'].astype(float).values,
                                   df_daycount_dc.loc[d].astype(float).values,
                                   df_forwards.loc[d].astype(float).values)

    # pnl from the positions, excluding the one that was just closed out
    previous_pnl = df_calc['pnl'].iloc[:-1].sum()

    # pnl for the current forwards
    if currency in ['JPY']:
        df_calc['pnl'] = - df_calc['notionals'] * (df_calc['fwd mtm'] - df_calc['fwd strike']) / df_calc['fwd mtm']
    else:
        df_calc['pnl'] = df_calc['notionals'] * (df_calc['fwd mtm']/df_calc['fwd strike'] - 1)


"""
* test JPY
"""
