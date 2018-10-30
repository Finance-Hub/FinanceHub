from fhdataapi import BBG
import pandas as pd

start_date = '30-mar-2015'
end_date = pd.to_datetime('today')

bbg = BBG()

# Grabs tickers and fields
df = bbg.fetch_series(securities=['BRL Curncy', 'DXY Index'],
                      fields=['PX_LAST', 'VOLATILITY_90D'],
                      startdate=start_date,
                      enddate=end_date)
print(df)

# Grabs cashflow payments of corporate bonds
df = bbg.fetch_cash_flow('EI1436001 Govt', pd.to_datetime('03-jul-2017'))
print(df)

# Grabs weights of the components of an index
df = bbg.fetch_index_weights(index_name='IBOV Index', ref_date=pd.to_datetime('03-jul-2017'))
print(df)
print(df.sum())

# Grabs a value
futures_list = bbg.fetch_futures_list(generic_ticker='TY1 Comdty')
print(futures_list)

# grabs the first notice date for each contract
df_fn = bbg.fetch_contract_parameter(securities=futures_list, field='FUT_NOTICE_FIRST')
print(df_fn)
