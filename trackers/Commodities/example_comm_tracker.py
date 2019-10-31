from trackers import CommFutureTracker
import matplotlib.pyplot as plt
from bloomberg import BBG
import pandas as pd

comm_bbg_code = 'lh'

# Calculate your own commodity tracker
comm = CommFutureTracker(comm_bbg_code)
comm_df = pd.pivot(comm.df_tracker, index='time_stamp', columns='fh_ticker', values='value')

# Get Bloomberg Commodity index (the 'BCOM' + comm_bbg_code + ' Index' will not work for every BCOM commodity)
bbg = BBG()
bbg_comm_raw = bbg.fetch_series(securities='BCOM' + comm_bbg_code.upper() + ' Index',
                                fields='PX_LAST',
                                startdate=comm_df.index[0].date(),
                                enddate=comm_df.index[-1].date())
bbg_comm_raw.columns = ['bcom_tracker']

bcom_index = pd.Series(index=comm_df.index)
bcom_index.iloc[0] = comm_df.iloc[0, 0]
for d in bcom_index.index[1:]:
    past_hist = bbg_comm_raw.loc[:d].copy()
    ret = past_hist.iloc[-1,0] / past_hist.iloc[-2, 0]
    bcom_index.loc[d] = bcom_index.loc[:d].iloc[-2] * ret

fig, ax = plt.subplots()
comm_df['comm us ' + comm_bbg_code.lower()].to_frame('my_index').dropna().plot(color='b', linewidth=3, ax=ax)
bcom_index.to_frame('bcom_index').plot(color='r', linewidth=1, ax=ax)
plt.title(comm_bbg_code.upper() + ' tracker')
plt.show()