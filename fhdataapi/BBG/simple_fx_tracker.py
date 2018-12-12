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
ann_factor = 252

#TODO add ['CNH', 'ILS'] to the list of currencies and deposit rates

currencies = [
    'EUR',
    'JPY',
    'GBP',
    'CHF',
    'CAD',
    'AUD',
    'NZD',
    'NOK',
    'SEK',
    'DKK',
    'CZK',
    'HUF',
    'ISK',
    'PLN',
    'SKK',
    'TRY',
    'ZAR',
    'HKD',
    'INR',
    'IDR',
    'PHP',
    'SGD',
    'KRW',
    'CNY',
    'MYR',
    'TWD',
    'THB',
    'ARS',
    'BRL',
    'CLP',
    'COP',
    'MXN',
    'PEN',
    'RUB'
]

deposit_rates_dict = {
    'EUR':'EUDRC',
    'JPY':'JYDRC',
    'GBP':'BPDRC',
    'CHF':'SFDRC',
    'CAD':'CDDRC',
    'AUD':'ADDRC',
    'NZD':'NDDRC',
    'NOK':'NKDRC',
    'SEK':'SKDRC',
    'DKK':'DKDRC',
    'CZK':'CKDRC',
    'HUF':'HFDRC',
    'ISK':'IKDRC',
    'PLN':'PZDRC',
    'SKK':'VKDRC',
    'TRY':'TYDRC',
    'ZAR':'SADRC',
    'HKD':'HDDRC',
    'INR':'IRDRC',
    'IDR':'IHDRC',
    'PHP':'PPDRC',
    'SGD':'SDDRC',
    'KRW':'KWDRC',
    'CNY':'CCNI3M',
    'MYR':'MRDRC',
    'TWD':'NTDRC',
    'THB':'TBDRC',
    'ARS':'APDRC',
    'BRL':'BCDRC',
    'CLP':'CHDRC',
    'COP':'CLDRC',
    'MXN':'MPDRC',
    'PEN':'PSDRC',
}

usd_dep_rate = bbg.fetch_series(securities=['USDRC BDSR Curncy'],
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)
usd_dep_rate.columns = ['usd_rate']

currencies = ['RUB','TWD','ZAR']

for currency in currencies:
    if currency not in ['RUB']:
        tickers = [currency + 'USD Curncy'] + [deposit_rates_dict[currency] + ' BDSR Curncy']
    else:
        tickers = ['RUBUSD Curncy','RRDRA Curncy'] if currency == 'RUB' else []

    # download the data from Bloomberg
    bbg_raw_data_df = bbg.fetch_series(securities=tickers,
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)
    bbg_raw_data_df.columns = ['spot','base_rate']
    bbg_raw_data_df = pd.concat([bbg_raw_data_df,usd_dep_rate,],join='outer',axis=1,sort=True)
    bbg_raw_data_df = bbg_raw_data_df.fillna(method='ffill').dropna()

    bbg_carry_index = bbg.fetch_series(securities = currency + 'USDCR CMPN Curncy',
                                   fields='PX_LAST',
                                   startdate=start_date,
                                   enddate=end_date)
    bbg_carry_index.columns = ['bbg_tracker']


    df = pd.DataFrame(index=bbg_raw_data_df.index,columns=['spot_index','carry_index','bbg_tracker'])
    df.iloc[0] = 100.
    for d in bbg_raw_data_df.index[1:]:
        fx_spot_ret = bbg_raw_data_df['spot'].loc[:d].iloc[-1]/bbg_raw_data_df['spot'].loc[:d].iloc[-2]
        df['spot_index'].loc[d] = df['spot_index'].loc[:d].iloc[-2] * fx_spot_ret

        long_carry_ret = 1 + (bbg_raw_data_df['base_rate'].loc[:d].iloc[-1]/100) / ann_factor
        short_carry_ret = 1 + (bbg_raw_data_df['usd_rate'].loc[:d].iloc[-1]/100) / ann_factor
        total_return = fx_spot_ret*long_carry_ret/short_carry_ret

        df['carry_index'].loc[d] = df['carry_index'].loc[:d].iloc[-2]*total_return

        bbg_tracker_ret = bbg_carry_index['bbg_tracker'].loc[:d].iloc[-1]/bbg_carry_index['bbg_tracker'].loc[:d].iloc[-2]
        df['bbg_tracker'].loc[d] = df['bbg_tracker'].loc[:d].iloc[-2] * bbg_tracker_ret

    df = df.fillna(method='ffill').dropna()

    df.plot()
    plt.title(currency)
    plt.show()