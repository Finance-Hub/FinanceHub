from dataapi import DI1
from sqlalchemy import create_engine

# ===== Create Connection =====
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


di = DI1(db_connect=db_connect)
print(di.build_df())

