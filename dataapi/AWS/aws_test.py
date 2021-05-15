from dataapi import TrackerFeeder, DBConnect, FocusFeeder
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import pandas as pd

db_connect = DBConnect('fhreadonly', 'finquant')

# ===== Exemples of the focus feeder =====
ff = FocusFeeder(db_connect)
df = ff.fetch('IPCA', 'yearly')
df.plot()
plt.show()

ff = FocusFeeder(db_connect)
df1 = ff.years_ahead('IPCA', 1)
df2 = ff.years_ahead('IPCA', 2)
df = pd.concat([df1, df2], axis=1)
df.plot()
plt.show()

# ===== Examples of the tracker feeder =====
tf = TrackerFeeder(db_connect)

# Fetch the full metadata table (useful for filtering)
df = tf.fetch_metadata()
print(df)

# fetch specific tickers
df = tf.fetch(['eqs br itub4', 'eqs us jpm'])
print(df)

# fetch assets with certain characteristics
filter_dict = {'sector': ['industrial', 'financial'],
               'country': 'BR'}
df = tf.filter_fetch(filter_dict, ret='series')
print(df)

# grab metadata possibilities
param_dict = tf.filter_parameters()
print(param_dict)

# grab all trackers
df = tf.fetch_everything()
df.plot()
plt.show()
