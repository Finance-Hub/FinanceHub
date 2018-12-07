from fhdataapi import BBG
import pandas as pd
from datetime import date, timedelta
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import math
import numpy as np

bbg = BBG()

start_date = pd.to_datetime('1999-01-04').date()
end_date = pd.to_datetime('today')

currency = 'AUD'
ann_factor = 252

tickers = [
    currency + 'USD Curncy', #this is the spot vs. the USD
    currency[0] + currency[2] + 'DRC BDSR Curncy', #this is the currency deposit rate
                                                   #most tickers are in that format, with just one or two exceptions                                                   # if you get nan for this, go to help wcrs <GO> on the bbg terminal
    'USDRC BDSR Curncy', #this is the USD deposit rate
]

# download the data from Bloomberg
bbg_raw_data_df = bbg.fetch_series(securities=tickers,
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)
bbg_raw_data_df.columns = ['spot','base_rate','usd_rate']
bbg_raw_data_df = bbg_raw_data_df.fillna(method='ffill')

df = pd.DataFrame(index=bbg_raw_data_df.index,columns=['spot_index','carry_index'])
df.iloc[0] = [100.,100.]

for d in bbg_raw_data_df.index[1:]:
    fx_spot_ret = bbg_raw_data_df['spot'].loc[:d].iloc[-1]/bbg_raw_data_df['spot'].loc[:d].iloc[-2]
    df['spot_index'].loc[d] = df['spot_index'].loc[:d].iloc[-2] * fx_spot_ret

    long_carry_ret = 1 + (bbg_raw_data_df['base_rate'].loc[:d].iloc[-1]/100) / ann_factor
    short_carry_ret = 1 + (bbg_raw_data_df['usd_rate'].loc[:d].iloc[-1]/100) / ann_factor
    total_return = fx_spot_ret*long_carry_ret/short_carry_ret

    df['carry_index'].loc[d] = df['carry_index'].loc[:d].iloc[-2]*total_return

bbg_carry_index = bbg.fetch_series(securities = currency + 'USDCR CMPN Curncy',
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)
bbg_carry_index.columns = ['bbg_tracker']


df = pd.concat([df,bbg_carry_index],join='outer',axis=1,sort=True).fillna(method='ffill').dropna()

df.plot()
plt.show()