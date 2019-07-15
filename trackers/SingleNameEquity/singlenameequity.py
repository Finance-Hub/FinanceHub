"""
Author: Gustavo Amarante
"""

import pandas as pd
from bloomberg import BBG
from pandas._libs.tslibs.nattype import NaTType


class SingleNameEquity(object):
    """
    Class for creating total return indices for single name equities using data from bloomberg. Assumes 1 stock held at
    oldest ex-dividend date and computes the total return index by reinvesting dividends on the same stock on every
    ex-dividend date.
    """

    def __init__(self, bbg_ticker, price_field='PX_LAST'):
        """
        Returns an object with the following attributes:
            - ticker: str with bloomberg ticker for the stock
            - dividends: DataFrame with dividend information. Its columns are 'Declared Date', 'Amount', 'Frequency',
                         'Type', 'Ex-Dividend Date', 'Payable Date', 'Record Date'
            - price: Series with the stock price
            - tr_index: Series with the total return index
            - quantity: amount of stocks held
            - ts_df: DataFrame with columns 'Price', 'Dividend', 'Quantity' and 'Total Return Index'
        :param bbg_ticker: str, Bloomberg ticker of the stock
        :param price_field: Price field to be used as settlement price
        """

        bbg = BBG()
        self.bbg_ticker = bbg_ticker

        today = pd.to_datetime('today')
        self.dividends = self._get_dividends(today, bbg)
        start_date_div = self.dividends['Ex-Dividend Date'].min()
        start_date_prc = pd.to_datetime(bbg.fetch_contract_parameter(self.bbg_ticker, 'CALENDAR_START_DATE').values[0][0])

        # Metadata to be saved
        self.country = bbg.fetch_contract_parameter(self.bbg_ticker, 'COUNTRY_ISO').iloc[0, 0].upper()
        self.exchange_symbol = bbg.fetch_contract_parameter(self.bbg_ticker, 'ID_EXCH_SYMBOL').iloc[0, 0]
        self.fh_ticker = 'eqs ' + self.country.lower() + ' ' + self.exchange_symbol.lower()
        self.asset_class = 'equity'
        self.type = 'stock'
        self.currency = bbg.fetch_contract_parameter(self.bbg_ticker, 'CRNCY').iloc[0, 0].upper()
        self.sector = bbg.fetch_contract_parameter(self.bbg_ticker, 'INDUSTRY_SECTOR').iloc[0, 0].lower()
        self.group = bbg.fetch_contract_parameter(self.bbg_ticker, 'INDUSTRY_GROUP').iloc[0, 0].lower()

        self.df_metadata = pd.DataFrame(data={'fh_ticker': self.fh_ticker,
                                              'asset_class': self.asset_class,
                                              'type': self.type,
                                              'exchange_symbol': self.exchange_symbol,
                                              'currency': self.currency,
                                              'country': self.country,
                                              'sector': self.sector,
                                              'group': self.group},
                                        index=[self.bbg_ticker])

        if isinstance(start_date_div, NaTType):
            start_date = start_date_prc
        else:
            start_date = min(start_date_div, start_date_prc)

        self.price = bbg.fetch_series(securities=bbg_ticker, fields=price_field, startdate=start_date, enddate=today)
        df = self._get_total_return_index()
        self.price = df[self.bbg_ticker].rename('Price')
        df['Price'] = self.price
        self.tr_index = df['Total Return Index'].rename('TR Index')
        self.quantity = df['Quantity'].rename('Quantity')
        self.df_ts = df[['Price', 'Dividend', 'Quantity', 'Total Return Index']]
        self.df_tracker = self._get_tracker_melted()

    def _get_tracker_melted(self):
        df = self.df_ts[['Total Return Index']].rename({'Total Return Index': self.fh_ticker}, axis=1)
        df['time_stamp'] = df.index.to_series()
        df = df.melt(id_vars='time_stamp', var_name='fh_ticker', value_name='value')
        df = df.dropna()

        return df

    def _get_dividends(self, today, bbg):
        df = bbg.fetch_dividends(self.bbg_ticker, today)

        rename_dict = {'Declared Date': 'Declared Date',
                       'Dividend Amount': 'Amount',
                       'Dividend Frequency': 'Frequency',
                       'Dividend Type': 'Type',
                       'Ex-Date': 'Ex-Dividend Date',
                       'Payable Date': 'Payable Date',
                       'Record Date': 'Record Date'}

        df = df.rename(rename_dict, axis=1)

        for col in ['Declared Date', 'Ex-Dividend Date', 'Payable Date', 'Record Date']:
            try:
                df[col] = pd.to_datetime(df[col])
            except KeyError:
                continue

        index2drop = df[df['Type'] == 'Quote Lot Change'].index
        df = df.drop(index2drop)

        index2drop = df[df['Type'] == 'Stock Split'].index
        df = df.drop(index2drop)

        index2drop = df[df['Type'] == 'Bonus'].index
        df = df.drop(index2drop)

        return df

    def _get_total_return_index(self):

        df = pd.DataFrame(index=self.dividends['Ex-Dividend Date'],
                          data={'Dividend': self.dividends['Amount'].values})

        df = df.join(self.price, how='outer')

        df['Dividend'] = df['Dividend'].fillna(0)
        df['Delta Stock'] = df['Dividend'] / df[self.bbg_ticker]

        df['Quantity'] = df['Delta Stock'].expanding().sum()+1

        df['Total Return Index'] = df['Quantity'] * df[self.bbg_ticker]

        df = df.loc[~df.index.duplicated(keep='last')]

        return df
