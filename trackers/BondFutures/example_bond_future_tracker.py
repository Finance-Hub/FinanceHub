"""
Author: Gustavo Amarante, Gustavo Soares
"""

from bloomberg import BBG
import pandas as pd
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import math

bbg = BBG()

start_date = (pd.to_datetime('2004-01-05') + BDay(1)).date()  # for the data
end_date = pd.to_datetime('today').date()

# value of the qoutes
df_generics = bbg.fetch_series(securities=['JB1 Comdty', 'JB2 Comdty', 'JB3 Comdty'],
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)

# underlying contracts
df_uc = bbg.fetch_series(securities=['JB1 Comdty', 'JB2 Comdty', 'JB3 Comdty'],
                         fields='FUT_CUR_GEN_TICKER',
                         startdate=start_date,
                         enddate=end_date)
df_uc = df_uc.reindex(df_generics.index).fillna(method='ffill')

# all contracts
contract_list = bbg.fetch_futures_list(generic_ticker='JB1 Comdty')

# first notice date for the contract
df_fn = bbg.fetch_contract_parameter(securities=contract_list, field='FUT_NOTICE_FIRST').sort_values('FUT_NOTICE_FIRST')

# Grab all contract series
contract_list = contract_list + ['JPYUSD Curncy']
df_prices = bbg.fetch_series(securities=contract_list,
                             fields='PX_LAST',
                             startdate=start_date,
                             enddate=end_date)
df_prices = df_prices.reindex(df_generics.index).fillna(method='ffill')

# sets up the dataframe that will hold our results
df_tracker = pd.DataFrame(index=df_generics.index,
                          columns=['contract_rolling_out', 'er_index', 'roll_out_date', 'holdings'])

# initialize
start_date = df_uc.index[0]

df_tracker.loc[start_date, 'er_index'] = 100

contract_rolling_out = df_uc.loc[start_date, 'JB2 Comdty'] + ' Comdty'
df_tracker.loc[start_date, 'contract_rolling_out'] = contract_rolling_out

holdings = df_tracker.loc[start_date, 'er_index'] / (df_generics.loc[start_date, 'JB2 Comdty'] * df_prices['JPYUSD Curncy'].loc[start_date])
df_tracker.loc[start_date, 'holdings'] = holdings

roll_out_date = df_fn.loc[df_tracker.loc[start_date, 'contract_rolling_out'], 'FUT_NOTICE_FIRST'] - BDay(1)
df_tracker.loc[start_date, 'roll_out_date'] = roll_out_date

# now for the rest of the dates
for d, dm1 in zip(df_tracker.index[1:], df_tracker.index[:-1]):
    print(d)
    df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out

    price_dm1 = df_prices.loc[dm1, contract_rolling_out]
    price_d = df_prices.loc[d, contract_rolling_out]
    pnl = holdings * (price_d - price_dm1) * df_prices['JPYUSD Curncy'].loc[d]

    if math.isnan(pnl):
        pnl = 0

    df_tracker.loc[d, 'er_index'] = df_tracker.loc[dm1, 'er_index'] + pnl

    if d >= roll_out_date.date():
        contract_rolling_out = (df_uc.loc[d, 'JB2 Comdty'] + ' Comdty')
        df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out

        holdings = df_tracker.loc[d, 'er_index'] / (df_generics.loc[d, 'JB2 Comdty'] * df_prices['JPYUSD Curncy'].loc[d])
        df_tracker.loc[d, 'holdings'] = holdings

        roll_out_date = df_fn.loc[df_tracker.loc[d, 'contract_rolling_out'], 'FUT_NOTICE_FIRST'] - BDay(1)
        df_tracker.loc[d, 'roll_out_date'] = roll_out_date

df_tracker['er_index'].plot()
plt.show()
