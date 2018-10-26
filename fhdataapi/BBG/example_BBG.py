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
df = bbg.fetch_cash_flow('EK026741@ANBE Corp', pd.to_datetime('03-jul-2017'))
print(df)

# Grabs weights of the components of an index
df = bbg.fetch_index_weights(index_name='IBOV Index', ref_date=pd.to_datetime('03-jul-2017'))
print(df)
