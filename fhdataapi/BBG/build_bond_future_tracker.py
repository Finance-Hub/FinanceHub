from fhdataapi import BBG
import pandas as pd
from datetime import timedelta
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import math

bbg = BBG()

sp_tracker_dict = {
    'US' : 'SPUSTTP',
    'GE' : 'SPEUBDP',
    'FR' : 'SPEUOAP',
    'IT' : 'SPEUBPP',
    'JP' : 'SPJGBER',
    'AU' : 'SPAUD10P',
    'UK' : 'SPUKGTP',
    'CA' : 'SPCACGP',
}

futures_ticker_dict = {
    'US': 'TY',
    'GE': 'RX',
    'FR': 'OAT',
    'IT': 'IK',
    'JP': 'JB',
    'AU': 'XM',
    'UK': 'G ',
    'CA': 'CN',
}

fx_dict = {'GE': 'EURUSD Curncy',
           'UK': 'GBPUSD Curncy',
           'CA': 'CADUSD Curncy',
           'JP': 'JPYUSD Curncy',
           'AU': 'AUDUSD Curncy',
           'FR': 'EURUSD Curncy',
           'IT': 'EURUSD Curncy',
           'US': 'USD Curncy'}

start_date = (pd.to_datetime('2004-01-05') + BDay(1)).date()  # for the data
end_date = pd.to_datetime('today').date()

for country in futures_ticker_dict.keys():
    # value of the qoutes
    futures_tickers = [futures_ticker_dict[country] + str(x) + ' Comdty' for x in range(1,4)]

    df_generics = bbg.fetch_series(securities=futures_tickers,
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)

    # underlying contracts
    df_uc = bbg.fetch_series(securities=futures_tickers,
                             fields='FUT_CUR_GEN_TICKER',
                             startdate=start_date,
                             enddate=end_date)
    df_uc = df_uc.reindex(df_generics.index).fillna(method='ffill')

    # all contracts
    contract_list = bbg.fetch_futures_list(generic_ticker=futures_ticker_dict[country] + '1 Comdty')

    # first notice date for the contract
    df_fn = bbg.fetch_contract_parameter(securities=contract_list, field='FUT_NOTICE_FIRST').sort_values('FUT_NOTICE_FIRST')

    # Grab all contract series
    contract_list = contract_list + [fx_dict[country]]
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

    contract_rolling_out = df_uc.loc[start_date, futures_ticker_dict[country] + '2 Comdty'] + ' Comdty'
    df_tracker.loc[start_date, 'contract_rolling_out'] = contract_rolling_out

    holdings = df_tracker.loc[start_date, 'er_index'] / (df_generics.loc[start_date, futures_ticker_dict[country] + '2 Comdty'] * df_prices[fx_dict[country]].loc[start_date])
    df_tracker.loc[start_date, 'holdings'] = holdings

    roll_out_date = df_fn.loc[df_tracker.loc[start_date, 'contract_rolling_out'], 'FUT_NOTICE_FIRST'] - BDay(1)
    df_tracker.loc[start_date, 'roll_out_date'] = roll_out_date

    # now for the rest of the dates
    for d, dm1 in zip(df_tracker.index[1:], df_tracker.index[:-1]):
        df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out

        price_dm1 = df_prices.loc[dm1, contract_rolling_out]
        price_d = df_prices.loc[d, contract_rolling_out]
        pnl = holdings * (price_d - price_dm1) * df_prices[fx_dict[country]].loc[d]

        if math.isnan(pnl):
            pnl = 0

        df_tracker.loc[d, 'er_index'] = df_tracker.loc[dm1, 'er_index'] + pnl

        if d >= roll_out_date.date():
            contract_rolling_out = (df_uc.loc[d, futures_ticker_dict[country] + '2 Comdty'] + ' Comdty')
            df_tracker.loc[d, 'contract_rolling_out'] = contract_rolling_out

            holdings = df_tracker.loc[d, 'er_index'] / (df_generics.loc[d, futures_ticker_dict[country] + '2 Comdty'] * df_prices[fx_dict[country]].loc[d])
            df_tracker.loc[d, 'holdings'] = holdings

            roll_out_date = df_fn.loc[df_tracker.loc[d, 'contract_rolling_out'], 'FUT_NOTICE_FIRST'] - BDay(1)
            df_tracker.loc[d, 'roll_out_date'] = roll_out_date

    sp_tracker = bbg.fetch_series(securities=[sp_tracker_dict[country] + ' Index'],
                                 fields='PX_LAST',
                                 startdate=start_date,
                                 enddate=end_date)
    if len(sp_tracker)!=0:

        if sp_tracker.index[0]<=df_tracker.index[0]:
            sp_tracker_index = pd.Series(index=df_tracker.index)
        else:
            sp_tracker_index = pd.Series(index=sp_tracker.index)
        sp_tracker_index.iloc[0] = df_tracker['er_index'].loc[:sp_tracker_index.index[0]].iloc[-1]

        for d,d_minus_1 in zip(sp_tracker_index.index[1:],sp_tracker_index.index[:-1]):
            ret = sp_tracker[:d].iloc[-1]/sp_tracker[:d_minus_1].iloc[-1] if d > sp_tracker.index[0] else 1
            sp_tracker_index[d] = sp_tracker_index[:d].iloc[-2]*ret

        df = pd.concat([df_tracker,sp_tracker_index.to_frame('sp_tracker')],
                       join='outer',axis=1,sort=True)
        df = df.fillna(method='ffill')

        df[['er_index','sp_tracker']].plot()
        plt.title('This is the bond futures tracker for %s' % country)
        plt.show()
    else:
        df = df_tracker.copy().fillna(method='ffill')

    writer = pd.ExcelWriter(r'G:\Gustavo Amarante\Aulas\df_' + country + '.xlsx')
    df.to_excel(writer)
    writer.save()
