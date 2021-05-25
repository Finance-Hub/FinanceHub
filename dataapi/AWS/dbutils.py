from sqlalchemy import create_engine


class DBConnect(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.connection = self._create_connection()

    def _create_connection(self):
        connect_dict = {'flavor': 'postgresql+psycopg2',
                        'database': 'labfinan',
                        'schema': 'public',
                        'user': self.username,
                        'password': self.password,
                        'host': 'labfinancas-01.c2q6rckdd916.us-east-1.rds.amazonaws.com',
                        'port': '5432'}

        db_connect = create_engine("{flavor}://{username}:{password}@{host}:{port}/{database}"
                                   .format(host=connect_dict['host'],
                                           database=connect_dict['database'],
                                           username=connect_dict['user'],
                                           password=connect_dict['password'],
                                           port=connect_dict['port'],
                                           flavor=connect_dict['flavor']))

        return db_connect
