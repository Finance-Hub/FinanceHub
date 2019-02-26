from fhdataapi import BBG
import pandas as pd
from datetime import timedelta
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import math

def get_contracts(d,contract_list,roll_schedule,comm_bbg_code):

    month_letter = roll_schedule[d.month-1] if roll_schedule[d.month-1].find('+')==-1 else roll_schedule[d.month-1][0]
    year_int = d.year if roll_schedule[d.month-1].find('+')==-1 else d.year + 1
    contract_rolling_out = comm_bbg_code + month_letter + str(year_int)[-2:] + ' Comdty'
    if contract_rolling_out not in contract_list:
        contract_rolling_out = comm_bbg_code + month_letter + str(year_int)[-1] + ' Comdty'

    d2 = d.replace(day=28) + timedelta(days=4)
    month_letter = roll_schedule[d2.month-1] if roll_schedule[d2.month-1].find('+')==-1 else roll_schedule[d2.month-1][0]
    year_int = d2.year if roll_schedule[d2.month-1].find('+')==-1 else d2.year + 1
    contract_rolling_in = comm_bbg_code + month_letter + str(year_int)[-2:] + ' Comdty'
    if contract_rolling_in not in contract_list:
        contract_rolling_in = comm_bbg_code + month_letter + str(year_int)[-1] + ' Comdty'

    return contract_rolling_out,contract_rolling_in

def get_contract_weights(d,calendar,roll_start_bday=5,roll_window_size=5,roll_type='standard'):
    days_in_the_month = [x for x in calendar if x.month == d.month and x.year == d.year]
    if roll_type == 'standard':
        start_idx = roll_start_bday - 1
        end_idx = roll_start_bday + roll_window_size - 2
        roll_start_date = days_in_the_month[start_idx] if len(days_in_the_month) > start_idx else days_in_the_month[-1]
        roll_end_date = days_in_the_month[end_idx] if len(days_in_the_month) > end_idx else days_in_the_month[-1]
    elif roll_type == 'backward_from_month_end':
        roll_start_date = days_in_the_month[roll_start_bday]
        roll_end_date = days_in_the_month[-1]

    if d < roll_start_date:
        weight_out = 1
    elif d > roll_end_date:
        weight_out = 0
    else:
        weight_out = float(len([x for x in days_in_the_month if x > d
                       and x <= roll_end_date])) / float(roll_window_size)

    return [weight_out, 1 - weight_out]

bbg = BBG()


start_date = (pd.to_datetime('2002-01-05') + BDay(1)).date()  # for the data
end_date = pd.to_datetime('today').date()

comm_bbg_code = 'CL'
roll_start_bday = 5
roll_window_size = 5
roll_schedule = ['H','K','K','N','N','U','U','X','X','F+','F+','H+']

writer = pd.ExcelWriter(r'G:\Gustavo Amarante\Aulas\df_' + comm_bbg_code + ' v2.xlsx')

# all contracts
contract_list = bbg.fetch_futures_list(generic_ticker=comm_bbg_code + '1 Comdty')

# first notice date for the contract
df_fn = bbg.fetch_contract_parameter(securities=contract_list, field='FUT_NOTICE_FIRST').sort_values('FUT_NOTICE_FIRST')
df_fn.to_excel(writer,'first_notice')

# Grab all contract series
df_prices = bbg.fetch_series(securities=contract_list,
                             fields='PX_LAST',
                             startdate=start_date,
                             enddate=end_date)
df_prices = df_prices.fillna(method='ffill')

df_prices.to_excel(writer,'prices')

# sets up the dataframe that will hold our results
back_start_date = df_prices.loc[df_prices.index[0].replace(day=28) + timedelta(days=4):].index[0] # start on 1st
                                                                                                  # bday of month
df_tracker = pd.DataFrame(index=df_prices.loc[back_start_date:].index,
                          columns=['contract_rolling_out', 'contract_rolling_in',
                                   'price_out_today', 'price_in_today','price_out_yst','price_in_yst',
                                   'w_out','w_in',
                                   'holdings_out','holdings_in',
                                   'er_index'])

# initialize
df_tracker.loc[back_start_date, 'er_index'] = 100

contract_rolling_out, contract_rolling_in = get_contracts(back_start_date,df_fn.index,roll_schedule,comm_bbg_code)
price_out = df_prices.loc[back_start_date,contract_rolling_out]
price_in = df_prices.loc[back_start_date,contract_rolling_in]
df_tracker.loc[back_start_date, 'contract_rolling_out'] = contract_rolling_out
df_tracker.loc[back_start_date, 'contract_rolling_in'] = contract_rolling_in
df_tracker.loc[back_start_date, 'price_out_today'] = price_out
df_tracker.loc[back_start_date, 'price_in_today'] = price_in

weights = get_contract_weights(back_start_date,df_prices.index,roll_start_bday=roll_start_bday,roll_window_size=roll_window_size)
df_tracker.loc[back_start_date, 'w_out'] = weights[0]
df_tracker.loc[back_start_date, 'w_in'] = weights[1]

holdings_out = weights[0]*df_tracker.loc[back_start_date, 'er_index']/price_out
holdings_in = weights[1]*df_tracker.loc[back_start_date, 'er_index']/price_in
holdings_out = 0 if math.isnan(holdings_out) else holdings_out
holdings_in = 0 if math.isnan(holdings_in) else holdings_in

df_tracker.loc[back_start_date, 'holdings_out'] = holdings_out
df_tracker.loc[back_start_date, 'holdings_in'] = holdings_in

for d, dm1 in zip(df_tracker.index[1:], df_tracker.index[:-1]):

    df_tracker.loc[d, 'w_out'] = weights[0]
    df_tracker.loc[d, 'w_in'] = weights[1]

    df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out
    df_tracker.loc[d, 'contract_rolling_in'] = contract_rolling_in

    price_out_d = df_prices[contract_rolling_out].loc[:d].iloc[-1]
    price_out_dm1 = df_prices[contract_rolling_out].loc[:d].iloc[-2]
    price_in_d = df_prices[contract_rolling_in].loc[:d].iloc[-1]
    price_in_dm1 = df_prices[contract_rolling_in].loc[:d].iloc[-2]

    df_tracker.loc[d, 'price_out_today'] = price_out_d
    df_tracker.loc[d, 'price_in_today'] = price_in_d

    df_tracker.loc[d, 'price_out_yst'] = price_out_dm1
    df_tracker.loc[d, 'price_in_yst'] = price_in_dm1

    df_tracker.loc[d, 'holdings_out'] = holdings_out
    df_tracker.loc[d, 'holdings_in'] = holdings_in

    if weights[1]==1:
        pnl = holdings_in * (price_in_d - price_in_dm1)
    else:
        pnl = holdings_in * (price_in_d - price_in_dm1) + holdings_out * (price_out_d - price_out_dm1)

    df_tracker.loc[d, 'er_index'] = df_tracker.loc[dm1, 'er_index'] + pnl

    contract_rolling_out, contract_rolling_in = get_contracts(d, df_fn.index, roll_schedule, comm_bbg_code)

    if d.month != dm1.month:
        holdings_out = holdings_in
        holdings_in = 0
        weights = [1,0]

        price_out_d = df_prices[contract_rolling_out].loc[:d].iloc[-1]
        price_out_dm1 = df_prices[contract_rolling_out].loc[:d].iloc[-2]
        price_in_d = df_prices[contract_rolling_in].loc[:d].iloc[-1]
        price_in_dm1 = df_prices[contract_rolling_in].loc[:d].iloc[-2]

        df_tracker.loc[d, 'holdings_out'] = holdings_out
        df_tracker.loc[d, 'holdings_in'] = holdings_in
        df_tracker.loc[d, 'w_out'] = weights[0]
        df_tracker.loc[d, 'w_in'] = weights[1]
        df_tracker.loc[d, 'price_out_today'] = price_out_d
        df_tracker.loc[d, 'price_in_today'] = price_in_d
        df_tracker.loc[d, 'price_out_yst'] = price_out_dm1
        df_tracker.loc[d, 'price_in_yst'] = price_in_dm1
        df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out
        df_tracker.loc[d, 'contract_rolling_in'] = contract_rolling_in

    else:

        weights = get_contract_weights(d, df_prices.index, roll_start_bday=roll_start_bday,
                                       roll_window_size=roll_window_size)

        holdings_out = weights[0] * df_tracker.loc[d, 'er_index'] / price_out_d
        holdings_in = weights[1] * df_tracker.loc[d, 'er_index'] / price_in_d
        holdings_out = 0 if math.isnan(holdings_out) else holdings_out
        holdings_in = 0 if math.isnan(holdings_in) else holdings_in

df = df_tracker.dropna(how='all')

df.to_excel(writer,'backtest')
writer.save()

