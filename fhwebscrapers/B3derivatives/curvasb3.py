import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
import time


class ScraperB3(object):
    """
    Scrapper for B3 prices. The key of this object is the `scrape` method.

    Supported contracts are:
        * DI1 - 1 day interbank deposits
        * DAP - DI x IPCA spread
        * DDI - DI x US Dollar spread
        * FRC - Forward Rate Agreement (FRA) on DI x US Dollar spread
        * DOL - US Dollar Futures
        * BGI - Live Cattle Futures (Options are not supported yet)
        * ICF - 4/5 Arabica Coffee Futures
        * CCM - Cash-Settled Corn Futures (Options are not supported yet)
        * AUD - Australian Dollar Futures
    """

    url = 'http://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-sistema-pregao-enUS.asp'

    # important string sequences for the scrapper
    key_string_center = '</tr><td class="text-center">'
    sep_string_center = '<td class="text-center">'
    sep_string_right = '<td class="text-right">'
    str_sep = '</td>'
    merc_identifier = 'MercFut3 = MercFut3 + '
    item_sep = ';'

    # Columns that are going to be parsed as values
    col2num = {'OPEN_INTEREST_OPEN', 'OPEN_INTEREST_CLOSE', 'NUMBER_OF_TRADES', 'TRADING_VOLUME', 'FINANCIAL_VOLUME',
               'PREVIOUS_SETTLEMENT', 'INDEXED_SETTLEMENT', 'OPENING_PRICE', 'MINIMUM_PRICE', 'MAXIMUM_PRICE',
               'AVERAGE_PRICE', 'LAST_PRICE', 'SETTLEMENT_PRICE', 'LAST_BID', 'LAST_OFFER'}

    # Columns that need to be dropped. They are either HTML junk or redundant information
    col2drop = {'JUNK1', 'CHANGE', 'VARIATION'}

    @staticmethod
    def scrape(contract, start_date, end_date, update_db=False, connect_dict=None):
        """

        :param contract: B3 code for the contract (see list of supported contracts)
        :param date: should be in american convention mm/dd/yyyy
        :param update_db: If True, updates the FinanceLab AWS database with the scraped data. Requires the connect_dict
                          property with the access credentials. Does not return a DataFrame as output.
        :param connect_dict: dict keys should be 'flavor', 'database', 'schema', 'user', 'password', 'host', 'port'.
                             These will generate the connection string.
        :return: DataFrame (if update_db is False) or None
        """

        if update_db:
            assert type(connect_dict) is dict, "If 'update_db' is True, 'connect_dict' should be a dictionary"

        if not (type(start_date) is str):
            start_date = start_date.strftime('%m/%d/%Y')
        else:
            start_date = pd.to_datetime(start_date).strftime('%m/%d/%Y')

        if not (type(end_date) is str):
            end_date = end_date.strftime('%m/%d/%Y')
        else:
            end_date = pd.to_datetime(end_date).strftime('%m/%d/%Y')

        df = pd.DataFrame()
        date_list = pd.date_range(start=start_date, end=end_date)

        for d in date_list:

            print('Scraping', contract, 'for date', d.strftime('%m/%d/%Y'))

            df_date = ScraperB3._scrape_single_date(contract, d.strftime('%m/%d/%Y'))
            df = pd.concat([df, df_date], join='outer')

        if update_db:
            ScraperB3._send_df_to_db(df, contract, connect_dict)

        else:
            return df

    @staticmethod
    def _scrape_single_date(contract, date):

        contract = contract.upper()
        header = ScraperB3._get_header(contract)

        df = pd.DataFrame(columns=header)

        resp_str = requests.get(ScraperB3.url, params={'Data': date, 'Mercadoria': contract}).text

        lkeyc = len(ScraperB3.key_string_center)
        lsepc = len(ScraperB3.sep_string_center)
        lsepr = len(ScraperB3.sep_string_right)

        isrunning = True

        while isrunning:
            if resp_str.find(ScraperB3.key_string_center) > -1:
                start_str = resp_str.find(ScraperB3.key_string_center)
                end_str = start_str + lkeyc + resp_str[start_str + lkeyc:].find(ScraperB3.merc_identifier)
                core = resp_str[start_str:end_str]
                core_v = core.split(ScraperB3.item_sep)
                resp_str = resp_str[end_str:]
                row_df = pd.DataFrame(index=[date], columns=header)

                i = 0
                for x in core_v[:-5]:
                    if x.find(ScraperB3.sep_string_center) > -1:
                        start_str = x.find(ScraperB3.sep_string_center) + lsepc
                        end_str = x.find(ScraperB3.str_sep)

                    elif x.find(ScraperB3.sep_string_right) > -1:
                        start_str = x.find(ScraperB3.sep_string_right) + lsepr
                        end_str = x.find(ScraperB3.str_sep)

                    to_add = x[start_str:end_str].replace(' ', '')

                    if to_add != '':
                        row_df[header[i]].loc[date] = to_add

                    i += 1

                df = df.append(row_df)

            else:
                isrunning = False

        df = ScraperB3._parse_str2num(df)
        df = ScraperB3._drop_useless_columns(df)
        df = ScraperB3._append_contract_column(contract, date, df)

        df.index = pd.to_datetime(df.index)

        if df.empty:  # TODO needs a better way to handle this error
            return
        else:
            return df

    @staticmethod
    def _get_header(contract):

        if contract in ['DI1', 'DAP', 'DDI']:
            header = ['MATURITY_CODE', 'OPEN_INTEREST_OPEN', 'OPEN_INTEREST_CLOSE', 'NUMBER_OF_TRADES',
                      'TRADING_VOLUME', 'FINANCIAL_VOLUME', 'JUNK1', 'PREVIOUS_SETTLEMENT', 'INDEXED_SETTLEMENT',
                      'OPENING_PRICE', 'MINIMUM_PRICE', 'MAXIMUM_PRICE', 'AVERAGE_PRICE', 'LAST_PRICE',
                      'SETTLEMENT_PRICE', 'CHANGE', 'LAST_BID', 'LAST_OFFER']

        elif contract in ['DOL', 'BGI', 'ICF', 'CCM', 'AUD']:
            header = ['MATURITY_CODE', 'OPEN_INTEREST_OPEN', 'OPEN_INTEREST_CLOSE', 'NUMBER_OF_TRADES',
                      'TRADING_VOLUME', 'FINANCIAL_VOLUME', 'JUNK1', 'OPENING_PRICE', 'MINIMUM_PRICE', 'MAXIMUM_PRICE',
                      'AVERAGE_PRICE', 'LAST_PRICE', 'SETTLEMENT_PRICE', 'CHANGE', 'LAST_BID', 'LAST_OFFER']

        elif contract in ['FRC']:
            header = ['MATURITY_CODE', 'NUMBER_OF_TRADES', 'TRADING_VOLUME', 'FINANCIAL_VOLUME', 'JUNK1',
                      'OPENING_PRICE', 'MINIMUM_PRICE', 'MAXIMUM_PRICE', 'AVERAGE_PRICE', 'LAST_PRICE',
                      'SETTLEMENT_PRICE', 'CHANGE', 'LAST_BID', 'LAST_OFFER']

        else:
            raise AttributeError(f'Contract {contract} is not available yet.')

        return header

    @staticmethod
    def _parse_str2num(df):

        cols_in_df = set(df.columns)
        cols_to_parse = cols_in_df & ScraperB3.col2num

        for col in cols_to_parse:
            df[col] = df[col].str.replace('[^0-9.]', '')  # argument is a RegEx
            df[col] = pd.to_numeric(df[col], errors='coerce')  # If unable to parse, is set to NaN

        return df

    @staticmethod
    def _drop_useless_columns(df):

        cols_in_df = set(df.columns)
        cols_to_drop = cols_in_df & ScraperB3.col2drop

        for col in cols_to_drop:
            df = df.drop(col, axis=1)

        return df

    @staticmethod
    def _append_contract_column(contract, date, df):

        add_col = pd.DataFrame(columns=['CONTRACT'], index=[date] * len(df), data=[contract] * len(df))

        df = pd.concat([add_col, df], axis=1)

        return df

    @staticmethod
    def _send_df_to_db(df, contract, connect_dict):

        start_time = time.time()

        df.columns = map(str.lower, df.columns)

        db_connect = create_engine("{flavor}://{username}:{password}@{host}:{port}/{database}"
                                   .format(host=connect_dict['host'],
                                           database=connect_dict['database'],
                                           username=connect_dict['user'],
                                           password=connect_dict['password'],
                                           port=connect_dict['port'],
                                           flavor=connect_dict['flavor']))

        min_date = df.index.min()
        max_date = df.index.max()

        query = 'SELECT time_stamp, maturity_code FROM "B3curvesteste" WHERE '
        query = query + f"contract='{contract}'"
        query = query + f"AND time_stamp BETWEEN '{min_date}' AND '{max_date}'"

        df_db = pd.read_sql(sql=query, con=db_connect, index_col='time_stamp')
        df_db = df_db.set_index([df_db.index, 'maturity_code'])

        df = df.set_index([df.index, 'maturity_code'])
        df = df.drop(df_db.index)
        df['maturity_code'] = df.index.get_level_values(1)
        df = df.set_index(df.index.get_level_values(0))

        try:
            df.to_sql('B3futures', con=db_connect, index=True, index_label='time_stamp', if_exists='append')

        except IntegrityError:
            print('There are duplicate entries in the DataFrame')

        print(round((time.time() - start_time)/60, 2), 'minutes to upload')


"""
TO DO
* treat weekends and holidays
* review documentation
* check if the example still works
"""
