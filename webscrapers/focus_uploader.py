from webscrapers import Focus
import matplotlib.pyplot as plt
import pandas as pd
from dataapi import DBConnect
from time import time

# ADD PATH TO YOUR CHROMEDRIVER
focus = Focus(r'/Users/gustavoamarante/Desktop/chromedriver')

# ADD DATABASE INFO
dbc = DBConnect('username', 'password')

# indicators to scrape and their frequency
indicators = {'ipca': ['monthly', 'yearly'],
              'pib': ['quarterly', 'yearly']}

rename_dict = {'Data': 'date'}

start_date = pd.to_datetime('2020-01-01')  # TODO query to find the latest date and correct the scrapper class to handle shorter periods
end_date = pd.to_datetime('today')

# loops all indicators and frequencies
for ind in indicators.keys():
    for freq in indicators[ind]:
        print(f'Scrapping {ind} with {freq} frequency')
        tic = time()
        df = focus.scrape(indicator=ind,
                          initial_date=start_date,
                          end_date=end_date,
                          frequency=freq)
        print(f'Scrapping took {(time() - tic) / 60} minutes')

        df = df.reset_index().melt(id_vars='Data', var_name='prediction_scope')

        df = df.rename(rename_dict, axis=1)

        df['index'] = ind
        df['frequency'] = freq
        df = df.dropna()

        print(f'Uploading {ind} with {freq} frequency')
        tic = time()
        df.to_sql(name='focus_survey', con=dbc.connection, index=False, method='multi', if_exists='append',
                  chunksize=200)
        print(f'Uploading took {(time() - tic)/60} minutes')
