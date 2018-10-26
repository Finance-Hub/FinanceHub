from fhdataapi import BBG
import pandas as pd
import numpy as np

start_date = pd.to_datetime('30-mar-2015')
end_date = pd.to_datetime('today')

bbg = BBG()

response = bbg.fetch_series(securities='BRL Curncy', fields='PX_LAST', startdate=start_date, enddate=end_date)

print(response)
