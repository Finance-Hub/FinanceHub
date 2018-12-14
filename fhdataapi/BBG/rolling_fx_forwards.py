from fhdataapi import BBG
import pandas as pd
import os
from datetime import date, timedelta
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import math
import numpy as np

bbg = BBG()

#TODO add ['DKK', 'ISK', 'SKK', 'HKD', 'CNY', 'MYR', 'THB', 'ARS', 'COP', 'PEN'] to the list of currencies

currencies = [
    'AUD',
    'BRL',
    'CAD',
    'CHF',
    'CLP',
    'CZK',
    'EUR',
    'GBP',
    'HUF',
    'JPY',
    'KRW',
    'MXN',
    'NOK',
    'NZD',
    'PHP',
    'PLN',
    'SEK',
    'SGD',
    'TRY',
    'TWD',
    'ZAR',
]

point_divisor_dict = {
    'AUD': 10000,
    'BRL': 10000,
    'CAD': 10000,
    'CHF': 10000,
    'CLP': 1,
    'CZK': 1000,
    'EUR': 10000,
    'GBP': 10000,
    'HUF': 100,
    'JPY': 100,
    'KRW': 1,
    'MXN': 10000,
    'NOK': 10000,
    'NZD': 10000,
    'PHP': 1,
    'PLN': 10000,
    'SEK': 10000,
    'SGD': 10000,
    'TRY': 10000,
    'TWD': 1,
    'ZAR': 10000,
}

print('We have %s currencies'% len(currencies))

quoted_as_XXXUSD = ['BRL','CAD','CHF','CLP','CZK','HUF',
                    'JPY','KRW','MXN','NOK','PHP','PLN',
                    'SGD','TRY','TWD','ZAR','SEK']

start_date = (pd.to_datetime('2004-01-05') + BDay(1)).date()  # for the data
end_date = pd.to_datetime('today').date()

#get spot FX rates
spot_tickers = [c + ' Curncy' for c in currencies]
bbg_raw_spot_data = bbg.fetch_series(securities=spot_tickers,
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)
bbg_raw_spot_data.columns = [x.replace(' Curncy','') for x in bbg_raw_spot_data.columns]
bbg_raw_spot_data = bbg_raw_spot_data.fillna(method='ffill')

#get 1M forwards
forward_tickers = [c + '1M Curncy' for c in currencies]
bbg_raw_fwd_data = bbg.fetch_series(securities=forward_tickers,
                               fields='PX_LAST',
                               startdate=start_date,
                               enddate=end_date)

bbg_raw_fwd_data.columns = [x.replace('1M Curncy','') for x in bbg_raw_fwd_data.columns]
bbg_raw_fwd_data = bbg_raw_fwd_data.fillna(method='ffill')
bbg_raw_spot_data.index = pd.to_datetime(bbg_raw_spot_data.index)
# get 1M NDFs
ndf_tickers = ['BCN1M Curncy','CHN1M Curncy','NTN1M BGN Curncy']
ndfs = bbg.fetch_series(securities=ndf_tickers,
                        fields='PX_LAST',
                        startdate=start_date,
                        enddate=end_date)
ndfs.columns = ['BRL','CLP','TWD']
ndfs = ndfs.fillna(method='ffill')
bbg_raw_fwd_data = bbg_raw_fwd_data.drop(ndfs.columns,1)
bbg_raw_fwd_data = pd.concat([bbg_raw_fwd_data,ndfs],join='outer',axis=1,sort=True)


#calculate forward outrights
fwd_outrights = bbg_raw_spot_data + bbg_raw_fwd_data/pd.Series(point_divisor_dict)
fwd_outrights.index = pd.to_datetime(fwd_outrights.index)
fwd_outrights = fwd_outrights.fillna(method='ffill')

#get all quotes vs. the USD
bbg_raw_spot_data[quoted_as_XXXUSD] = 1/bbg_raw_spot_data[quoted_as_XXXUSD]
fwd_outrights[quoted_as_XXXUSD] = 1/fwd_outrights[quoted_as_XXXUSD]

#calculate carry indices using DC 30/365 convention for accrual
carry_indices = pd.DataFrame(index=fwd_outrights.index,
                             columns=fwd_outrights.columns)
start_date = fwd_outrights.index[0]
carry_indices.loc[start_date] = 100.
strikes = fwd_outrights.loc[start_date]
holdings = 100./strikes
settlement_date = start_date + timedelta(days=30) + BDay(2)
last_rebalance = start_date
for d in carry_indices.index[1:]:
    day_count = (settlement_date - d).days
    fwd_mtm = pd.Series(index=currencies)
    for c in currencies:
        s = bbg_raw_spot_data[c].loc[:d].iloc[-1]
        f = fwd_outrights[c].loc[d]
        fwd_mtm[c] = np.interp(float(day_count),[2,32],[s,f])

    carry_indices.loc[d] = carry_indices.loc[last_rebalance] + holdings * (fwd_mtm - strikes)

    if d>=settlement_date:
        strikes = fwd_outrights.loc[d]
        holdings = carry_indices.loc[d] / strikes
        settlement_date = d + timedelta(days=30) + BDay(2)
        last_rebalance = d

#plot each carry index for each currency
for c in carry_indices.columns:
    print(c)
    # Bloomberg trackers
    bbg_carry_raw = bbg.fetch_series(securities=c + 'USDCR CMPN Curncy',
                                       fields='PX_LAST',
                                       startdate=start_date.date(),
                                       enddate=end_date)
    bbg_carry_raw.columns = ['bbg_tracker']

    bbg_carry_index = pd.Series(index=carry_indices[c].dropna().index)
    bbg_carry_index.iloc[0] = carry_indices[c].loc[:bbg_carry_index.index[0]].iloc[-1]
    for d in bbg_carry_index.index[1:]:
        ret = carry_indices[c].loc[d]/carry_indices[c].loc[:d].iloc[-2]
        bbg_carry_index.loc[d] = bbg_carry_index.loc[:d].iloc[-2]*ret

    fig, ax = plt.subplots()
    carry_indices[c].to_frame('my_index').dropna().plot(color='b', linewidth= 3, ax=ax)
    bbg_carry_index.to_frame('bbg_index').plot(color='r', linewidth=1, ax=ax)
    plt.title(c)
    plt.show()

