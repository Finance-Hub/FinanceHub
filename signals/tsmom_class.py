"""
Author: Eduardo Minatel Tinos and Eduardo Ribeiro da Silva
"""

import pandas as pd
from pandas.tseries.offsets import BDay


def momentum(df,h=252):
    '''
    Computes the momentum signal for all the series in a dataframe
    :param df: pandas dataframe or series
    :param h: lookback period in business days
    :return: pandas dataframe with the momentum signals
    '''

    df.index = pd.to_datetime(df.index)
    df_mom = df.pct_change(freq=BDay(h))

    return df_mom


def macd(df, hl_rap=12, hl_len=26):
    '''
    Computes the macd signal for all the series in a dataframe
    :param df: pandas dataframe or series
    :param hl_rap: lookback period in business days for the fast exponential moving average
    :param hl_len: lookback period in business days for the slow exponential moving average
    :return: pandas dataframe with the macd signals
    '''

    assert hl_rap < hl_len, 'hl_rap should be lower than hl_len'

    df_rap = df.ewm(halflife=hl_rap).mean()
    df_len = df.ewm(halflife=hl_len).mean()
    df_macd = df_rap - df_len

    return df_macd


def relative_position(df, h):
    '''
    :param df: pandas dataframe or series
    :param h: lookback period in business days
    :return: pandas dataframe with the relative position signals
    '''

    
    df_min = df.rolling(h).min()
    df_max = df.rolling(h).max()
    
    df_rp = (df-df_min)/(df_max-df_min)
    
    return df_rp


def relative_strength_index(df, h=14):
    '''
    :param df: pandas dataframe or series
    :param h: lookback period in business days
    :return: pandas dataframe with the momentum signals
    '''

    # Calculates daily price change from t to t+1
    df_delta = df.diff().dropna()
    
    up, down = df_delta.copy(), df_delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    roll_up1 = up.rolling(h).sum()
    roll_down1 = down.rolling(h).sum().abs()

    df_rs = roll_up1 / roll_down1
    df_rsi = 100 - 100 / (1 + df_rs)

    return df_rsi
