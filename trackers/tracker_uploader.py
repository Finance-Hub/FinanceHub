from trackers import SingleNameEquity

connect_dict = {'flavor': 'postgres+psycopg2',
                'database': '[DATABASE NAME]',
                'schema': '[DATABASE SCHEMA]',
                'user': '[USERNAME]',
                'password': '[PASSWORD]',
                'host': '[HOST ADDRESS]',
                'port': '[PORT NUMBER]'}

stocks = ['PETR4 BZ Equity']

for s in stocks:
    sne = SingleNameEquity(s)
