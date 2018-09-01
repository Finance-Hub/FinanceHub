import pandas as pd
import requests


class ScraperB3(object):

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

    # Columns that need to be dropped
    col2drop = {'JUNK1', 'CHANGE', 'VARIATION'}

    @staticmethod
    def scrape(contract, date):

        header = ScraperB3._get_header(contract)

        if not (type(date) is str):
            date = date.strftime('%m/%d/%Y')

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

        return df

    @staticmethod
    def _get_header(contract):

        if contract in ['DI1']:
            header = ['MATURITY_CODE', 'OPEN_INTEREST_OPEN', 'OPEN_INTEREST_CLOSE', 'NUMBER_OF_TRADES',
                      'TRADING_VOLUME', 'FINANCIAL_VOLUME', 'JUNK1', 'PREVIOUS_SETTLEMENT', 'INDEXED_SETTLEMENT',
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
