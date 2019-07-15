"""
This is a maintenance routine for the database
Author: Gustavo Amarante
"""

from webscrapers import ScraperB3Derivatives
import pandas as pd
import time

start_time = time.time()

connect_dict = {'flavor': 'postgres+psycopg2',
                'database': '[DATABASE NAME]',
                'schema': '[DATABASE SCHEMA]',
                'user': '[USERNAME]',
                'password': '[PASSWORD]',
                'host': '[HOST ADDRESS]',
                'port': '[PORT NUMBER]'}

b3 = ScraperB3Derivatives(connect_dict)

month_start = pd.date_range(start='01/01/2009',
                            end='12/31/2009',
                            freq='MS')

month_end = pd.date_range(start='01/01/2009',
                          end='12/31/2009',
                          freq='M')

for dt_ini, dt_end in zip(month_start, month_end):

    print(dt_ini.month_name())

    df = b3.scrape(contract='DAP',
                   start_date=dt_ini,
                   end_date=dt_end,
                   update_db=True)

print(round((time.time() - start_time)/60, 2), 'minutes to run everything')
