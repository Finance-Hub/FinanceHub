from fhdataapi import BBG
import pandas as pd
from datetime import date, timedelta
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import math
import numpy as np


bbg = BBG()

start_date = pd.to_datetime('1999-01-04').date()
end_date = (pd.to_datetime('2015-04-29')).date()
currency = 'AUD'

tickers = [
    currency + ' Curncy',   #This is the ticker for the XXXUSD spot exchange rate'
    currency + '1W Curncy', #This is the ticker for the XXXUSD 1 week forward rate in pts'
    currency + '1M Curncy', #This is the ticker for the XXXUSD 1 month forward rate in pts'
    currency + '2M Curncy', #This is the ticker for the XXXUSD 2 month forward rate in pts'
]

# download the data from bloomberg
bbg_raw_data_df = bbg.fetch_series(securities=tickers,
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)

bbg_raw_data_df.columns = ['spot','1w','1m','2m']

day_count_dc = [0,7,30,60] #these are the number of days for spot, 1 week, 1 month, and 2 month

#this is going to store the settlement dates and the outright forwards
value_dates = pd.DataFrame(index=bbg_raw_data_df.index,columns=bbg_raw_data_df.columns)
forwards = pd.DataFrame(index=bbg_raw_data_df.index,columns=bbg_raw_data_df.columns)
for i in range(len(day_count_dc)):
    #since the trade settle 2 business days afterwards, we take the settlement date for each of the cases and
    value_dates[bbg_raw_data_df.columns[i]] = bbg_raw_data_df.index + timedelta(days=day_count_dc[i]) + BDay(2)
    if i !=0: #if not spot, get the outright forwards by dividing the points by 10000
        forwards[forwards.columns[i]] = bbg_raw_data_df['spot'] + bbg_raw_data_df.iloc[:,i]/10000
    else:
        forwards[forwards.columns[i]] = bbg_raw_data_df['spot']

#this is going to store the day count between the foward and the spot settlement dates
day_counts_df = pd.DataFrame(index=value_dates.index,columns=['spot'],data=0)
for i in value_dates.columns[1:]:
    day_counts_df[i] = [(a - b).days for a, b in zip(value_dates[i], value_dates['spot'])]

#We are going to build a trading stratey in which we every day trade a fraction of the notional on a 1 month forward
number_of_trades = 21 #so, we get a strip of forwards
how_much_pct_of_notional_to_trade_per_day = 1./float(number_of_trades)

pnl = pd.Series(index=range(number_of_trades), data=0.)
fwd_mtm = pd.Series(index=range(number_of_trades), data=0.)
fwd_strikes = pd.Series(index=range(number_of_trades), data=0.)
fwd_day_count = pd.Series(index=range(number_of_trades), data=0.)
notionals = pd.Series(index=range(number_of_trades), data=0.)

#this is going to store the maturity of the foward being traded
days_to_mat_new_position = pd.Series(index=value_dates.index[:-number_of_trades],
                                     data=[(a-b).days for a,b in zip(value_dates['1m'].iloc[number_of_trades:],
                                                                     value_dates['1m'].iloc[:-number_of_trades])])

#start the tracker index with 100 notional
tracker_index = pd.Series(index=value_dates.index[:-number_of_trades])
index_start_date = tracker_index.index[0]
tracker_index.iloc[0] = 100.

for d,d_minus_1 in zip(tracker_index.index[1:],tracker_index.index[:-1]):
    # move all trades down one position
    fwd_day_count.iloc[1:] = fwd_day_count.iloc[:-1].values
    notionals.iloc[1:] = notionals.iloc[:-1].values
    fwd_strikes.iloc[1:] = fwd_strikes.iloc[:-1].values

    # insert the data for the new trade
    fwd_day_count.iloc[0] = days_to_mat_new_position[d_minus_1] -\
                            (value_dates['spot'][d]-value_dates['spot'][d_minus_1]).days
    notionals.iloc[0] = tracker_index[d_minus_1]*how_much_pct_of_notional_to_trade_per_day
    fwd_strikes.iloc[0] = np.interp(float(days_to_mat_new_position[d]),
                                    list(day_counts_df.loc[d].astype(float).values),
                                    list(forwards.loc[d].values))

    # mark to market the forwards that we are holding
    fwd_mtm = pd.Series(index=fwd_strikes.index,
                        data=np.interp(list(fwd_day_count.values),
                        list(day_counts_df.loc[d].astype(float).values),
                        list(forwards.loc[d].values)))

    # this is the pnl since the forwards were struke yesterday, excluding the trade that was closed out
    # the pnl of the trade done today is zero
    previous_pnl_sum = pnl.iloc[:-1].sum()

    # this is the pnl since the forwards were struke
    pnl = notionals*(fwd_mtm/fwd_strikes-1.)

    todays_pnl = (pnl.sum() - previous_pnl_sum) #this is how much money was made today
    tracker_index[d] = tracker_index[d_minus_1] + todays_pnl #acumulate the pnl in the tracker


bbg_carry_index = bbg.fetch_series(securities = currency + 'USDCR CMPN Curncy',
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)
bbg_carry_index.columns = ['bbg_tracker']

spot_index = pd.Series(index=tracker_index.index)
spot_index.iloc[0] = tracker_index.iloc[0]
for d in spot_index.index[1:]:
    spot_ret = bbg_raw_data_df['spot'].loc[:d].iloc[-1] / bbg_raw_data_df['spot'].loc[:d].iloc[-2]
    spot_index[d] = spot_index.loc[:d].iloc[-2]*(spot_ret)

df = pd.concat([bbg_carry_index,
                spot_index.to_frame('spot_index'),
                tracker_index.to_frame('my_tracker')],
               join='outer',axis=1,sort=True).fillna(method='ffill').dropna()

df.plot()
plt.show()





