from fhdataapi import BBG
import pandas as pd

start_date = pd.to_datetime('30-mar-2015')
end_date = pd.to_datetime('today')

bbg = BBG()

df = bbg.fetch_series(securities=['BRL Curncy', 'DXY Index'],
                      fields=['PX_LAST', 'VOLATILITY_90D'],
                      startdate=start_date,
                      enddate=end_date)

print(df)
