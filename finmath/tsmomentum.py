import pandas as pd
from pandas.tseries import offsets


def momentum(df, h=252):

    df.index = pd.to_datetime(df.index)
    df_mom = df.pct_change(freq=offsets.BDay(h))

    return df_mom


def macd(df, m1=12, m2=26):

    assert m1 < m2, "m1 must smaller than m2"

    df.index = pd.to_datetime(df.index)

    df_m1 = df.ewm(halflife=m1, adjust=True).mean()
    df_m2 = df.ewm(halflife=m2, adjust=True).mean()
    df_macd = df_m1 - df_m2

    return df_macd
