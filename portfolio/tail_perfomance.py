"""
Module to obtain vol-ajdusted performance on (user specified) drawdowns.
User may specify to use non-overlapping (fixed window) or all available drawdowns.
"""

import pandas as pd
import numpy as np
import calendars
import logging
from calendars import DayCounts

def tail_risk_table(index_ts: Union[pd.Series, pd.DataFrame],
                    ref_index: Union[pd.Series, pd.DataFrame],
                    freq: str = 'daily',
                    same_window: bool = True,
                    window: Optional[int] = None,
                    k: Optional[int] = None,
                    summary_table: Optional[bool] = True,
                    annualize_ret: bool = True) -> pd.DataFrame:
    """
    Calculates vol-adjusted performance in tail risk events of reference benchmark index

    Arguments
    ----------
        index_ts: Pandas Series or DataFrame
             Daily time series data for performance calculation.

        ref_index: Pandas Series or DataFrame 
            Daily time series data for reference benchmark index. 
            If DataFrame has more than one column, the first column will be used as reference benchmark index.

        freq: str (default = 'Daily')
            Frequencies available: daily, weekly, monthly 
        
        same_window: bool (default = True)
            If true, it indicates whether the performance metrics are to be calculated for all columns in the index_ts DataFrame over the same time frame.
            or, just using as much data as possible for each column. 

        window: int (Optional)
            Window size for fixed window dd calculation. 
            Defaults to computing unrestricted drawdowns.

        k: int (Optional)
            Maximum number of drawdowns to use in calculations. 
            Defaults to using all available drawdowns.

        summary_table: bool (Optional, default = True)
            If true, it indicates whether the function should return a summary of performance metrics
            or the performance for each of the drawdowns.

        annualize_ret: bool (default = True)
            If true, indicates whether returns should be annualized.

    Returns
    --------
        Pandas DataFrame with performance in tail risk events of the reference benchmark index containing:

            - Mean reactivity: average performance in tail risk events
            - Median reactivity: median performance in tail risk events
            - Reliability: frequency of positive performance in tail risk events
            - Convexity: median performance minus first quartile performance in tail risk events
            - Tail beta: conditional beta to reference benchmark index in tail risk events but subtracting the unconditional means instead of conditional means
            - Avg carry: unconditional average performance
            - Carry in recovery: average performance during the period of recovery (only calculated for unrestricted drawdown)
            - Start date: is the start date of the first drawdown
            - End date: is the end date of the last drawdown
    """

    logger = logging.getLogger(_name_)

    # Series/DataFrame check
    if isinstance(index_ts, pd.Series):
        index_ts = index_ts.dropna().astype(float).to_frame('index_ts')
    if isinstance(ref_index, pd.Series):
        ref_index = ref_index.dropna().astype(float).to_frame('ref_index')
    elif isinstance(ref_index, pd.DataFrame):
        ref_index = ref_index.iloc[:, [0]].dropna().astype(float)
    else:
        msg = "'ref_index' must be a Pandas Series or DataFrame"
        logger.error(msg)
        raise TypeError(msg)

    df = pd.concat([ref_index, index_ts], join='outer', axis=1, sort=True).fillna(method='ffill')
    df = df.dropna(how='any' if same_window else 'all')

    # Volatility, Mean (vol. adjusted)
    freq_dict = {'daily': 21, 'weekly': 4, 'monthly': 1}
    vols = np.log(df).diff(freq_dict[freq]).std() * np.sqrt(12.)
    mus = (np.log(df).diff(freq_dict[freq]) * 12.).mean().div(vols)

    if window:
        dd = _window_dd_single(df.iloc[:, 0], window=window) # Fixed window drawdown
        ann_factor = 252. / float(window)
    else:
        dd = _unr_dd_single(df.iloc[:, 0])                   # Unrestricted drawdown
        ann_factor = None
    if k:
        dd = dd.iloc[:k]

    # Drawdown log returns
    start_dates = dd.index.get_level_values(level=0)
    end_dates = dd.index.get_level_values(level=1)
    p1 = df.loc[end_dates].values
    p0 = df.loc[start_dates].values
    log_ret = np.log((p1 / p0).squeeze())
    log_ret = pd.DataFrame(columns=df.columns, data=log_ret)

    # DayCounts
    dc = DayCounts('ACT/360', calendar='us_trading')
    if ann_factor is None:
        range_d1_d0 = dc.days(start_dates, end_dates)
        ann_factor = [365.25 / float(d) for d in range_d1_d0]
        ann_factor = pd.Series(index=log_ret.index, data=ann_factor)

        recovery_end_dates = dd.index.get_level_values(level=2)
        p1 = df.iloc[:, 1:].loc[end_dates].values
        p0 = df.iloc[:, 1:].loc[recovery_end_dates].values
        recovery_ret = np.log((p0 / p1).squeeze())
        recovery_ret = pd.DataFrame(columns=df.columns[1:], data=recovery_ret)
        range_d1_d0 = dc.days(end_dates, recovery_end_dates)
        recovery_ann_factor = [365.25 / float(d) if float(d)>3. else np.nan for d in range_d1_d0]
        recovery_ann_factor = pd.Series(index=recovery_ret.index, data=recovery_ann_factor)

        if annualize_ret:
            recovery_ret = recovery_ret.multiply(recovery_ann_factor, axis=0).div(vols.iloc[1:])
        else:
            recovery_ret = recovery_ret.div(vols.iloc[1:])

        recovery_carry = recovery_ret.mean()
    else:
        recovery_carry = None
        recovery_ret = None

    if annualize_ret:
        log_ret = log_ret.multiply(ann_factor, axis=0).div(vols)
    else:
        log_ret = log_ret.div(vols)

    ref_ind_ret = log_ret.iloc[:, 0]
    log_ret = log_ret.iloc[:, 1:]

    n = log_ret.count()
    table = pd.DataFrame(index=log_ret.columns)
    table['mean_reactivity'] = log_ret.mean()
    table['median_reactivity'] = log_ret.median()
    table['reliability'] = log_ret[log_ret > 0].count().div(n)
    q3_minus_q1 = log_ret.quantile(q=0.80) - table['median_reactivity']
    table['convexity(80%-50%)'] = q3_minus_q1

    ref_ret_minus_unc_mean = ref_ind_ret - mus.iloc[0]
    ret_minus_unc_mean = log_ret.subtract(mus.iloc[1:])
    xy_cov = ret_minus_unc_mean.multiply(ref_ret_minus_unc_mean, axis=0).mean()
    y_var = ref_ret_minus_unc_mean.var()
    table['tail_beta'] = xy_cov / y_var
    table['avg_carry'] = mus.iloc[1:]
    if isinstance(recovery_carry, pd.Series):
        table['recovery_carry'] = recovery_carry
    table['start_date'] = [min(df[x].dropna().index).strftime('%d-%b-%y') for x in df.columns[1:]]
    table['end_date'] = [max(df[x].dropna().index).strftime('%d-%b-%y') for x in df.columns[1:]]
    table = table.T
    table.index.name = '%sbd_dd' % window if window else 'unr_dd'

    if summary_table:
        return table
    else:
        log_ret.index = dd.index
        if isinstance(recovery_ret, pd.DataFrame):
            recovery_ret.index = dd.index
            log_ret = log_ret.stack().to_frame('drawdown')
            recovery_ret = recovery_ret.stack().to_frame('recovery')
            log_ret = pd.concat([log_ret, recovery_ret], join='outer', axis=1, sort=True)
            log_ret = log_ret.unstack()
        return log_ret

def _window_dd_single(index_ts: Union[pd.Series, pd.DataFrame],
                      window: int) -> pd.Series:
    """
    Calculates fixed window non-overlapping drawdowns for given time series data

    Arguments
    ----------
        index_ts: Pandas Series or DataFrame 
            A single column with daily data. 
            If DataFrame has more than one column, the first column will be used to calculate drawdowns.

        window: int
            Window size for fixed window drawdown calculation.

    Returns
    --------
        Pandas Series:
            Contains the tuple (start date, end date), as a multi-level index and the drawdown itself as values.
    """

    logger = logging.getLogger(_name_)

    if isinstance(index_ts, pd.Series):
        index_ts = index_ts.dropna().astype(float)
    elif isinstance(index_ts, pd.DataFrame):
        index_ts = index_ts.iloc[:, 0].dropna().astype(float)
    else:
        msg = "'index_ts' must be a Pandas Series or DataFrame"
        logger.error(msg)
        raise TypeError(msg)

    window_dd = index_ts.pct_change(window).to_frame('dd')
    window_dd['end_date'] = window_dd.index
    window_dd['start_date'] = window_dd['end_date'].shift(window)
    window_dd = window_dd[window_dd['dd'] < 0].dropna()
    non_overlap_dd = pd.DataFrame()

    while len(window_dd) > 0:
        min_index = window_dd['dd'].idxmin()
        case = window_dd.loc[[min_index]]
        non_overlap_dd = non_overlap_dd.append(case)
        sd = case['start_date'].values[0]
        ed = case['end_date'].values[0]

        no_overlap_mask = (window_dd['start_date'] >= ed) | \
                          (window_dd['end_date'] <= sd)
        window_dd = window_dd[no_overlap_mask]

    return non_overlap_dd.set_index(['start_date', 'end_date']).iloc[:, 0]

def _unr_dd_single(index_ts: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    """
    Calculates all drawdowns for given time series data.

    Arguments
    ----------
        index_ts: Pandas Series or DataFrame
            A single column with daily data.
            If DataFrame has more than one column, the first column will be used to calculate drawdowns.

    Returns
    --------
        Pandas Series:
            Contains the tuple (peak date, end date, trough date) as a multi-level index and the drawdown itself as values.
    """

    logger = logging.getLogger(_name_)

    if isinstance(index_ts, pd.Series):
        index_ts = index_ts.dropna().astype(float)
    elif isinstance(index_ts, pd.DataFrame):
        index_ts = index_ts.iloc[:, 0].dropna().astype(float)
    else:
        msg = "'index_ts' must be a Pandas Series or DataFrame"
        logger.error(msg)
        raise TypeError(msg)

    previous_peaks = index_ts.expanding(min_periods=1).max()
    bad_times = previous_peaks.drop_duplicates().to_frame('peak')
    bad_times['peak_dates'] = bad_times.index
    bad_times = bad_times.reset_index(drop=True)
    bad_times['end_dates'] = np.nan
    bad_times['trough'] = np.nan
    bad_times['trough_dates'] = np.nan
    bad_times['dd'] = np.nan

    for i in bad_times.index:
        p = bad_times.loc[i, 'peak']
        d = bad_times.loc[i, 'peak_dates']
        recovery_data = index_ts.loc[d:][index_ts.loc[d:] > p]
        if len(recovery_data) > 0:
            ed = recovery_data.index[0]
        else:
            ed = index_ts.index[-1]
        bad_times.loc[i, 'end_dates'] = ed
        bad_times.loc[i, 'trough'] = index_ts.loc[d:ed].min()
        bad_times.loc[i, 'trough_dates'] = index_ts.loc[d:ed].idxmin()

    bad_times['dd'] = bad_times['trough'] / bad_times['peak'] - 1.
    bad_times = bad_times[bad_times['dd'] < 0.].drop(['peak', 'trough'], 1)
    bad_times = bad_times.set_index(['peak_dates', 'trough_dates', 'end_dates'])

    return bad_times.iloc[:, 0].sort_values()