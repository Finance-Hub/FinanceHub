from bloomberg import BBG
import matplotlib.pyplot as plt
from portfolio.backtesting_functions import FHSignalBasedWeights
import pandas as pd
import numpy as np


start_date = '30-mar-2000'
end_date = pd.to_datetime('today')

bbg = BBG()

# Grabs tickers and fields
df = bbg.fetch_series(securities='SPVXMP Index',
                      fields='PX_LAST',
                      startdate=start_date,
                      enddate=end_date)

df2 = bbg.fetch_series(securities='SPUSSOUT Index',
                       fields='PX_LAST',
                       startdate=start_date,
                       enddate=end_date)

df3 = bbg.fetch_series(securities='SPDAUDT Index',
                       fields='PX_LAST',
                       startdate=start_date,
                       enddate=end_date)

df4 = bbg.fetch_series(securities='BXIICSTU Index',
                       fields='PX_LAST',
                       startdate=start_date,
                       enddate=end_date)

ts = pd.concat([df, df2, df3, df4], axis=1, sort=True).dropna(how='all').astype(float)

mom_signals = np.log(ts).diff(252).dropna(how='all')

b = FHSignalBasedWeights(ts, mom_signals, rebalance='Y')
b.run_backtest('mom_backtest').plot()
plt.show()