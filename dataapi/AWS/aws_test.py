from dataapi import TrackerFeeder
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

connect_dict = {'flavor': 'postgres+psycopg2',
                'database': '[DATABASE NAME]',
                'schema': '[DATABASE SCHEMA]',
                'user': '[USERNAME]',
                'password': '[PASSWORD]',
                'host': '[HOST ADDRESS]',
                'port': '[PORT NUMBER]'}

db_connect = create_engine("{flavor}://{username}:{password}@{host}:{port}/{database}"
                           .format(host=connect_dict['host'],
                                   database=connect_dict['database'],
                                   username=connect_dict['user'],
                                   password=connect_dict['password'],
                                   port=connect_dict['port'],
                                   flavor=connect_dict['flavor']))

# ===== Examples =====
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
