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
    'CNH',
    'CZK',
    'EUR',
    'GBP',
    'HUF',
    'IDR',
    'ILS',
    'INR',
    'JPY',
    'KRW',
    'MXN',
    'NOK',
    'NZD',
    'PHP',
    'PLN',
    'RUB',
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
    'CNH': 10000,
    'CZK': 1000,
    'EUR': 10000,
    'GBP': 10000,
    'HUF': 100,
    'IDR': 1,
    'ILS': 10000,
    'INR': 100,
    'JPY': 100,
    'KRW': 1,
    'MXN': 10000,
    'NOK': 10000,
    'NZD': 10000,
    'PHP': 1,
    'PLN': 10000,
    'RUB': 10000,
    'SEK': 10000,
    'SGD': 10000,
    'TRY': 10000,
    'TWD': 1,
    'ZAR': 10000,
}

print('We have %s currencies'% len(currencies))

quoted_as_XXXUSD = ['BRL','CAD','CHF','CLP','CZK','HUF','IDR','ILS',
                    'INR','JPY','KRW','MXN','NOK','PHP','PLN','RUB',
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

#get 1M NDFs
ndf_tickers = ['BCN1M Curncy','CHN1M Curncy','IHN1M Curncy','IRN1M Curncy','NTN1M BGN Curncy']
ndfs = bbg.fetch_series(securities=ndf_tickers,
                        fields='PX_LAST',
                        startdate=start_date,
                        enddate=end_date)
ndfs.columns = ['BRL','CLP','IDR','INR','TWD']
ndfs = ndfs.fillna(method='ffill')
bbg_raw_fwd_data = bbg_raw_fwd_data.drop(ndfs.columns,1)
bbg_raw_fwd_data = pd.concat([bbg_raw_fwd_data,ndfs],join='outer',axis=1,sort=True)

#calculate forward outrights
fwd_outrights = bbg_raw_spot_data + bbg_raw_fwd_data/pd.Series(point_divisor_dict)

#get all quotes vs. the USD
bbg_raw_spot_data[quoted_as_XXXUSD] = 1/bbg_raw_spot_data[quoted_as_XXXUSD]
fwd_outrights[quoted_as_XXXUSD] = 1/fwd_outrights[quoted_as_XXXUSD]

#calculate carry indices using DC 30/365 convention for accrual
carry_indices = pd.DataFrame(index=fwd_outrights.index,
                             columns=fwd_outrights.columns)
carry_indices.iloc[0] = 100.
for d in carry_indices.index[1:]:
    spot_return = bbg_raw_spot_data.loc[:d].iloc[-1]/bbg_raw_spot_data.loc[:d].iloc[-2]-1
    implied_carry = ((1/365)*np.log((bbg_raw_spot_data.loc[:d].iloc[-2]/fwd_outrights.loc[:d].iloc[-2])**(365/30)))
    returns = spot_return+implied_carry
    carry_indices.loc[d] = (carry_indices.loc[:d].iloc[-2] * (1 + returns.fillna(0))).values

#plot each carry index for each currency
for c in carry_indices.columns:
    carry_indices[[c]].plot()
    plt.title(c)
    plt.show()

