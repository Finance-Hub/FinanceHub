from fhdataapi import BBG
import pandas as pd

start_date = pd.to_datetime('30-mar-2015')
end_date = pd.to_datetime('today')

bbg = BBG()

bbg.fetch_series()
