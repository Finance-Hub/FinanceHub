"""

Module to obtain information on monthly and annual returns of a DataFrame,
in addition, other analyzes are performed on the data

"""

import pandas as pd
import numpy as np

adju_factor_dict = {'daily': 252.0, 'weekly': 52.0, 'monthly': 12.0}


def expanding_dd(ser):
    max2here = ser.expanding(min_periods=1).max()
    dd2here = ser/max2here - 1.0
    return dd2here


def max_dd(ser):
    dd2here = expanding_dd(ser)
    return dd2here.min()


def get_perf_table_single(df_ts: pd.Series,
                          name_col: str = 'perf_table',
                          freq: str = 'daily') -> pd.DataFrame:
    """
    Returns a pandas dataframe with performance metrics for a particular
    times series (assumed to be cumulative excess returns)

    Args:
        df_ts (pd.Series): A time series where the index is the measurement time
        name_col (str): The name of the output column
        freq (str): Choose a frequency

    Returns:
        pd.DataFrame: DataFrame with performance metrics
    """
    clean_index_series = df_ts.copy()

    adju_factor = adju_factor_dict[freq]

    table = pd.Series(dtype = object)
    table['frequency'] = freq
    table['excess_returns'] = (clean_index_series[-1] / clean_index_series[0]) ** \
                              (adju_factor / (len(clean_index_series) - 1.0)) - 1

    log_returns = np.log(clean_index_series).diff(1).dropna()
    table['volatility'] = log_returns.std() * np.sqrt(adju_factor)
    table['sharpe'] = table['excess_returns'] / table['volatility']
    table['sortino'] = table['excess_returns'] / (np.sqrt(adju_factor) * (log_returns[log_returns < 0.0]).std())

    table['maxDD'] = max_dd(clean_index_series)
    table['maxDD_to_vol_ratio'] = max_dd(clean_index_series) / table['volatility']

    table['from_date'] = clean_index_series.index[0].strftime('%d-%b-%y')
    table['to_date'] = clean_index_series.index[-1].strftime('%d-%b-%y')
    table['n_obs'] = len(clean_index_series)
    df_ = table.to_frame(name_col)

    return df_


def get_perf_table(df: pd.DataFrame,
                   freq: str = 'daily',
                   same_window: bool = True) -> pd.DataFrame:
    """
    Returns a pandas dataframe with performance metrics for a set of
    times series (assumed to be cumulative excess returns) as columns of a
    pandas dataframe

    Args:
        df (pd.DataFrame): A time series data
        freq (str): Define the frequency
        same_window (bool): A bool to define if all columns will be returned in the same time window

    Returns:
        pd.DataFrame: DataFrame with performance metrics
    """
    df_ts = df.copy()
    if same_window:
        df_ts.dropna(inplace = True)

    tables = []
    for column_name in df_ts.columns:
        table = get_perf_table_single(df_ts[column_name], name_col = column_name, freq = freq)

        tables.append(table)
    df_ = pd.concat(tables, axis = 1)

    return df_


def get_3T_sharpe_stats_single(
        ts_series: pd.Series,
        name_col: str = 'sharpe_over_3_periods',
        freq: str = 'daily') -> pd.DataFrame:
    """
    Returns a pandas dataframe with descriptive stats for the 3y rolling
    Sharpe ratio of a pandas series

    Args:
        ts_series (pd.Series): A time series where the index is the measurement time
        name_col (str): The desired name for the column that will be formed at the end of
                        processing. Defaults to '3T'.
        freq (str): Define the frequency

    Returns:
        pd.DataFrame: DataFrame with Sharpe ratio descriptive stats
    """
    clean_index_series = ts_series.copy()

    adju_factor = adju_factor_dict[freq]

    returns_3T:pd.Series = (1. + clean_index_series.pct_change(int(
        adju_factor * 3.))) ** (1. / 3.) - 1.
    vol_3T = np.log(clean_index_series).diff(1).rolling(window = int(adju_factor * 3.)).std() * np.sqrt(adju_factor)
    hist_3T_sharpe = ((returns_3T / vol_3T).dropna()).describe()
    hist_3T_sharpe['freq'] = freq
    hist_3T_sharpe['from_date'] = returns_3T.index[0].strftime('%d-%b-%y')
    hist_3T_sharpe['to_date'] = returns_3T.index[-1].strftime('%d-%b-%y')
    df_ = hist_3T_sharpe.to_frame(name_col)

    return df_


def get_3T_sharpe_stats(df: pd.DataFrame, freq: str = 'daily', same_window: bool = True) -> pd.DataFrame:
    """
    Returns a pandas dataframe with descriptive stats for the 3y rolling
    Sharpe ratio of the columns of a pandas dataframe

    Args:
        df (pd.Series): A time series where the index is the measurement time
        freq (str): Define the frequency
        same_window (bool): A bool to define if all columns will be returned in the same time window

    Returns:
        pd.DataFrame: DataFrame with Sharpe ratio descriptive stats
    """
    df_ts = df.copy()
    if same_window:
        df_ts.dropna(inplace = True)

    tables = []
    for column_name in df_ts.columns:
        table = get_3T_sharpe_stats_single(df_ts[column_name].dropna().sort_index(), name_col = column_name,
                                           freq = freq)
        tables.append(table)
    df_ = pd.concat(tables, axis = 1)

    return df_


def get_yearly_sharpe_single(ts_series: pd.Series, name_col='yearly_sharpe') -> pd.DataFrame:
    """
    A function to, given a time series, analyze the sharpe year by year

    Args:
        ts_series (pd.Series): A time series where the index is the measurement time
        name_col (str, optional): The desired name for the column that will be formed at the end of
                                  processing. Defaults to 'yearly_sharpe'.

    Returns:
        pd.DataFrame: A DataFrame pandas with the index being the detected years of the time series
                      and its column (name_col) with their respective sharpes
    """
    clean_dates_arr = ts_series.resample('M').last().pct_change(1).dropna().reset_index().to_numpy()


    to_year = np.vectorize(lambda x: x.year)
    years_arr = to_year(clean_dates_arr[:,0])
    unique_years_arr = np.sort(np.unique(years_arr))

    sharpe_arr = np.empty(unique_years_arr.shape[0])

    for i in range(unique_years_arr.shape[0]):

        year = unique_years_arr[i]

        year_calendar = clean_dates_arr[years_arr == year, 1]

        ret = (1 + year_calendar).prod() ** (12 / year_calendar.shape[0]) - 1

        vol = np.std(year_calendar) * np.sqrt(12)

        sharpe_arr[i] = ret/vol

    data = {
        'years' : unique_years_arr,
        name_col: sharpe_arr
    }

    df_ = pd.DataFrame(data).set_index('years')

    return df_


def get_yearly_sharpe(df_ts: pd.DataFrame) -> pd.DataFrame:
    """
    Similar to the get_yearly_sharpe_single method,
    however, it is now possible to parse a DataFrame completely

    Args:
        df_ts (pd.DataFrame): A DataFrame where its index is the dates of its measurements and the
                              columns present their respective values

    Returns:
        pd.DataFrame: A DataFrame with the annual analysis of each of the columns
    """

    cols = df_ts.columns

    tables = np.empty(cols.shape[0], dtype=np.object)

    for i, case in enumerate(cols):

        table = get_yearly_sharpe_single(df_ts[case], name_col=case)

        tables[i] = table

    df_ = pd.concat(tables,axis=1)

    return df_


def get_monthly_return_table_single(
        ts_series: pd.Series,
        index_name='perf_table',
        merge_month_table=True
    ) -> pd.DataFrame:
    """
    Function to obtain the monthly return of a time series

    Args:
        ts_series (pd.Series): A time series where the index is the measurement time

        index_name (str, optional): Name of the indexes that will be created for the final result.
                                    Defaults to 'perf_table'.

        merge_month_table (bool, optional): If so, month measurements will be attached in result.
                                            Defaults to True.

    Returns:
        pd.DataFrame: DataFrame with analysis of monthly input returns
    """

    clean_ts_arr = ts_series.resample('M').last().pct_change(1).dropna().reset_index().to_numpy()

    to_year = np.vectorize(lambda x: x.year)

    years = to_year(clean_ts_arr[:, 0])

    unique_years = np.sort(np.unique(years))

    ret_arr = np.empty(unique_years.shape[0])
    vol_arr = np.empty_like(ret_arr)

    for i in range(unique_years.shape[0]):

        year = unique_years[i]

        year_calendar_arr = clean_ts_arr[years == year, 1]

        ret_arr[i] = np.product( 1 + year_calendar_arr ) ** (12 / year_calendar_arr.shape[0]) - 1

        vol_arr[i] = np.std(year_calendar_arr) * np.sqrt(12)

    sharpe_arr = ret_arr / vol_arr

    yearly_data = {
        'year': unique_years,
        'ret': ret_arr,
        'vol': vol_arr,
        'sharpe': sharpe_arr
    }

    df_yearly_sharpe = pd.DataFrame(yearly_data).set_index('year')

    if merge_month_table:
        to_month = np.vectorize(lambda x: x.month)

        months = to_month(clean_ts_arr[:, 0])

        unique_monts = np.sort(np.unique(months))

        df_month = pd.DataFrame(index=unique_years, columns=unique_monts)

        for idx, val in clean_ts_arr:
            df_month.loc[idx.year, idx.month] = val

        out = pd.concat([df_month, df_yearly_sharpe], axis=1)

    else:
        out = df_yearly_sharpe

    out.index.name = index_name

    return out


def _choose_metric_function(key: str):
    """
    Auxiliary function for choosing a metric

    Args:
        key (str): Key word for choosing a metrics

    Returns:
        function: implementation of the desired metrics
    """
    out = lambda x: x

    if key == 'mean':
        out = lambda x: x.mean()

    elif key == 'median':
        out = lambda x: x.median()

    elif key == 'sharpe':
        out = lambda x: x.mean()/x.std()

    elif key == 'q1':
        out = lambda x: x.quantile(q=.25)

    elif key == 'q3':
        out = lambda x: x.quantile(q=.75)

    elif key == 'p10':
        out = lambda x: x.quantile(q=.10)

    elif key == 'p90':
        out = lambda x: x.quantile(q=.90)

    return out


def get_qq_table_single(
        index_ts: pd.Series,
        ref_index: pd.Series,
        metric='mean',
        index_name='quintiles'
    ) -> pd.DataFrame:
    """
    Calculates descriptive stats (metric) of index_ts in different
    quantiles of ref_index

    Args:
        index_ts (pd.Series): time series of cumulative returns) for the
        asset to be analyzed
        ref_index (pd.Series): time series of cumulative returns) for the
        reference asset
        metric (str, optional): Metric of interest. Defaults to 'mean'.
        Options are: 'mean', 'median', 'sharpe', 'q1', 'q3', 'p10' and 'p90'
        index_name (str, optional): column name for the returning dataframe,
        it defaults to 'quintiles'.

    Returns:
        pd.DataFrame: Contains the descriptive stats (metric) of
        index_ts in different quantiles of ref_index
    """


    if isinstance(index_ts, pd.core.series.Series):
        clean_index_series = index_ts.copy()
    else:
        index_name = index_ts.columns[0]
        clean_index_series = index_ts[index_name].copy()

    if isinstance(ref_index, pd.core.series.Series):
        clean_ref_index_series = ref_index.copy()
    else:
        index_name = ref_index.columns[0]
        clean_ref_index_series = ref_index[index_name].copy()

    df = pd.concat([clean_ref_index_series,clean_index_series],join='outer',axis=1).fillna(method='ffill')
    ret = df.pct_change(1).dropna()

    metric_function = _choose_metric_function(metric)    

    q1 = ret.iloc[:, 0].quantile(q=.2)
    q2 = ret.iloc[:, 0].quantile(q=.4)
    q3 = ret.iloc[:, 0].quantile(q=.6)
    q4 = ret.iloc[:, 0].quantile(q=.8)

    quintis = pd.Series(index=['q1', 'q2', 'q3', 'q4', 'q5'])

    quintis['q1'] = metric_function(ret[ret.iloc[:, 0] <= q1].iloc[:, 1])
    quintis['q2'] = metric_function(ret[q1 <= ret.iloc[:, 0]][ret.iloc[:, 0] <= q2].iloc[:, 1])
    quintis['q3'] = metric_function(ret[q2 <= ret.iloc[:, 0]][ret.iloc[:, 0] <= q3].iloc[:, 1])
    quintis['q4'] = metric_function(ret[q3 <= ret.iloc[:, 0]][ret.iloc[:, 0] <= q4].iloc[:, 1])
    quintis['q5'] = metric_function(ret[q4 <= ret.iloc[:, 0]].iloc[:, 1])
    quintis['from_date'] = df.index[0].strftime('%d-%b-%y')
    quintis['to_date'] = df.index[-1].strftime('%d-%b-%y')

    return quintis.to_frame(index_name)
