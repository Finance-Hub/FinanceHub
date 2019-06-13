"""
Author: Gustavo Amarante
"""

import pandas as pd
from bloomberg import BBG


class SingleNameEquity(object):
    """
    Class for creating total return indeces for single name equities. Assumes 1 stock held at oldest ex-dividend date
    and computes the total return indedx by reinvesting dividends on the same stock on every ex-dividend date.
    """

    def __init__(self, ticker, price_field='PX_LAST'):
        """
        Returns an object with the following atributes:
            - ticker: str with bloomberg ticker for the stock
            - dividends: DataFrame with dividend information. Its columns are 'Declared Date', 'Amount', 'Frequency',
                         'Type', 'Ex-Dividend Date', 'Payable Date', 'Record Date'
            - price: Series with the stock price
            - tr_index: Series with the total return index
            - quantity: amount of stocks held
            - ts_df: DataFrame with columns 'Price', 'Dividend', 'Quantity' and 'Total Return Index'
        :param ticker: str, Bloomberg ticker of the stock
        :param price_field: Price field to be used as settlement price
        """

        # TODO Handle case where there are no dividend payments
        # TODO Debug case for AAPL US Equity

        bbg = BBG()
        self.ticker = ticker
        today = pd.to_datetime('today')
        self.dividends = self._get_dividends(today, bbg)
        start_date = self.dividends['Ex-Dividend Date'].min()
        self.price = bbg.fetch_series(securities=ticker, fields=price_field, startdate=start_date, enddate=today)
        df = self._get_total_return_index()
        self.price = df[self.ticker].rename('Price')
        df['Price'] = self.price
        self.tr_index = df['Total Return Index'].rename('TR Index')
        self.quantity = df['Quantity'].rename('Quantity')
        self.ts_df = df[['Price', 'Dividend', 'Quantity', 'Total Return Index']]

    def _get_dividends(self, today, bbg):
        df = bbg.fetch_dividends(self.ticker, today)

        rename_dict = {'Declared Date': 'Declared Date',
                       'Dividend Amount': 'Amount',
                       'Dividend Frequency': 'Frequency',
                       'Dividend Type': 'Type',
                       'Ex-Date': 'Ex-Dividend Date',
                       'Payable Date': 'Payable Date',
                       'Record Date': 'Record Date'}

        df = df.rename(rename_dict, axis=1)

        for col in ['Declared Date', 'Ex-Dividend Date', 'Payable Date', 'Record Date']:
            df[col] = pd.to_datetime(df[col])

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
        df['Delta Stock'] = df['Dividend'] / df[self.ticker]

        df['Quantity'] = df['Delta Stock'].expanding().sum()+1

        df['Total Return Index'] = df['Quantity'] * df[self.ticker]

        return df
