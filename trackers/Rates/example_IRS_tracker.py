from trackers import FwdIRSTrackers
import pandas as pd
import matplotlib.pyplot as plt

IRS = FwdIRSTrackers(ccy='AUD', tenor=5)
my_tracker = IRS.df_tracker
my_tracker.plot()
plt.show()

