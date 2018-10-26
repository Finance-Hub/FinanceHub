from fhdataapi import BBG
import pandas as pd

start_date = '30-mar-2015'
end_date = pd.to_datetime('today')

bbg = BBG()

df = bbg.fetch_series(securities=['BRL Curncy', 'DXY Index'],
                      fields=['PX_LAST', 'VOLATILITY_90D'],
                      startdate=start_date,
                      enddate=end_date)

df2 = bbg.fetch_cash_flow('EK026741@ANBE Corp', pd.to_datetime('03-jul-2017'))

print(df2)
