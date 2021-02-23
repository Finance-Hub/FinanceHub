import pandas as pd
import numpy as np
from pandas.tseries.offsets import *
import scipy.optimize as opt
import scipy.cluster.hierarchy as sch
from scipy import stats


class FHBacktestAncilliaryFunctions(object):
    """
    This class contains a set of ancilliary supporting functions for performing backtests.
    They are all static methods meant to be used some place else.

    Here is the current list of methods:

    resample_dates : for calculating rebalancing dates based on Pandas calendar sampling
    expand_static_weights : to transfor static weights series in a dataframe of constant weights over some time index
    get_cov_matrix_on_date : calculates covariance matrices
    static_weights : static non-negative weights (long-only) for a given weighting scheme

    """

    @staticmethod
    def resample_dates(index, rebalance):
        """ This function resamples index (a DatetimeIndex) in a few different ways:
        1. Using the double-letter codes below:
            # WW        weekly frequency (on Wednesdays)
            # WF        weekly frequency (on Fridays)
            # WM        weekly frequency (on Mondays)
            # ME        month end frequency (last day of the month)
            # MM        mid-month frequency (10th business days of the month)
            # MS        month start frequency (first day of the month)
            # QE        quarter end frequency
            # QM        quarter end mid-month frequency (10th business days of the end of quarter month)
            # QS        quarter start frequency (first day of the quarter)
            # SE        semester end frequency
            # SM        semester end mid-month frequency (15th of June and 15th of December)
            # SS        semester start frequency
            # YE        year end frequency
            # YM        year end mid-month frequency (15th of December)
            # YS        year start frequency (first day of the year)
        2. Given a custom list or DatetimeIndex with custom rebalancing dates
        3. Given a list of months to rebalance as in [2,4,8] for rebalancing in Feb, Apr, and Aug
        If the function fails to recognize the resampling method, it will assume ME"""
        if isinstance(rebalance, str):
            if (rebalance[0] == 'W' and len(rebalance) > 1) or rebalance == 'W':
                wd = int(2 * (rebalance[1] == 'W') + 4 * (rebalance[1] == 'F')) if len(rebalance) > 1 else None
                rebc = pd.to_datetime([x for x in (index + Week(1, weekday=wd)).unique()])
            elif rebalance == 'ME' or rebalance == 'M':
                rebc = pd.to_datetime((index + BMonthEnd(1)).unique())
            elif rebalance == 'MM':
                rebc = pd.to_datetime((index + MonthBegin(0) + BusinessDay(10)).unique())
            elif rebalance == 'MS':
                # TODO: This is taking the last business day of the month if index + MonthBegin(0) fall on a weekend. Fix this.
                rebc = pd.to_datetime((index + MonthBegin(0)).unique())
            elif rebalance == 'QE' or rebalance == 'Q':
                rebc = pd.to_datetime((index + QuarterEnd(1)).unique())
            elif rebalance == 'QM':
                rebc = pd.to_datetime((index + QuarterBegin(0) + BusinessDay(10)).unique())
            elif rebalance == 'QS':
                # TODO: This is taking the last business day of the quarter if index + QuarterBegin(0) fall on a weekend. Fix this.
                rebc = pd.to_datetime((index + QuarterBegin(0)).unique())
            elif rebalance == 'SE' or rebalance == 'S':
                rebc = pd.to_datetime([x for x in (index + BMonthEnd(1)).unique() if x.month in [6, 12]])
            elif rebalance == 'SM':
                rebc = pd.to_datetime(
                    [x for x in (index + MonthBegin(0) + BusinessDay(10)).unique() if x.month in [6, 12]])
            elif rebalance == 'SS':
                # TODO: This is taking the last business day of the semester if index + MonthBegin(0) fall on a weekend. Fix this.
                rebc = pd.to_datetime([x for x in (index + MonthBegin(0)).unique() if x.month in [6, 12]])
            elif rebalance == 'YE' or rebalance == 'Y':
                rebc = pd.to_datetime((index + BYearEnd(1)).unique())
            elif rebalance == 'YM':
                rebc = pd.to_datetime((index + BYearBegin(0) + BusinessDay(10)).unique())
            elif rebalance == 'YS':
                # TODO: This is taking the last business day of the semester if index + MonthBegin(0) fall on a weekend. Fix this.
                rebc = pd.to_datetime((index + BYearBegin(0)).unique())
            else:
                print('rebalance string not recognized, assuming month end frequency (last day of the month)')
                rebc = pd.to_datetime((index + BMonthEnd(1)).unique())
        elif isinstance(rebalance, list):
            if all(isinstance(x, type(index[0])) for x in
                   rebalance):  # if the list or DatetimeIndex contains actual dates
                rebc = pd.to_datetime(rebalance)
            else:
                # this will work if the user provided a list with months to rebalance month end frequency (last day of the month
                try:
                    rebc = pd.to_datetime([x for x in (index + BMonthEnd(1)).unique() if x.month in rebalance])
                except:  # last resort for user provided list
                    print('Invalid rebalance list, assuming month end frequency (last day of the month)')
                    rebc = pd.to_datetime((index + BMonthEnd(1)).unique())
        else:
            print('rebalance parameter not recognized, assuming month end frequency (last day of the month)')
            rebc = pd.to_datetime((index + BMonthEnd(1)).unique())

        # not necessarily the rebalancing days are valid days, i.e., are in index
        # we need to take the rebalancing days that are not in index and alter them
        # we alter them to the closest possible date in index
        # rebalancing days that are not in index
        rebc.freq = None
        notin = pd.DatetimeIndex([x for x in rebc if x not in index and x < index.max()],
                                                                        dtype=rebc.dtype, freq=rebc.freq)

        # find the closest day in index
        if isinstance(rebalance, str) and len(rebalance) == 2 and rebalance[1] == 'S':
            # when dealing with start frequency we want to find the next valid day not only the closest
            next_index_day = lambda x: min([d for d in index if d >= x])
            alter = [next_index_day(p) for p in notin]
        else:
            # for the other cases, we just find the closest date
            alter = [min(index, key=lambda x: abs(x - p)) for p in notin]

        notin = notin.append(pd.DatetimeIndex([x for x in rebc if x > index.max()], dtype=rebc.dtype, freq=rebc.freq))

        alter = pd.DatetimeIndex(alter, dtype=rebc.dtype, freq=rebc.freq)
        reb = rebc.drop(notin)  # drop the invalid rebalancing dates
        reb = reb.append(alter)  # add the closest days in index
        reb = reb.sort_values()  # reorder

        return reb

    @staticmethod
    def expand_static_weights(dates_to_expand, weights):
        """"
        This function transforms static weights in a dataframe of constant weights having dates_to_expand as index
        """
        w_df = pd.DataFrame(index=dates_to_expand,
                            columns=weights.index,
                            data=np.tile(weights.values, [len(dates_to_expand), 1]))
        return w_df

    @staticmethod
    def get_cov_matrix_on_date(d, ts, h=21, cov_type='rolling', cov_window=756, halflife=60, shrinkage_parameter = 1):
        """
            This function calculates the annualized covariance matrix for a given date, r
            It does a few things that are important for backtests that are not done by pandas cov functions

            1.It will take the unconditional cov matrix if there is too little data (less than cov_window bdays)
              This avoids using cov estimates with just a few datapoints (less than cov_window bdays) in the backtest
            2.The DataFrame ts can have time series starting a different points in time
              The cov estimates will use the pairwise unconditional coveriance matrix if there is too little data given

            Parameters
            ----------
            r :  a single date value of the same type as the dates in ts.index
            ts : a DataFrame with daily time series of index/price levels (not returns!)
            h :  this is the number of bdays used to calculate returns for estimating the covariance matrix
            cov_type : is a string with the type of covariance calulation it can be:
                1. rolling (default) : is a rolling window of size cov_window (default is 3 years of data)
                2. ewma : is a ewma cov (default halflife is 60 bdays)
                3. expanding : is an expanding window from the start of each series

            Returns
            -------
            an annualized covariance matrix based on h period returns

        """

        # clean up
        ts = ts.astype(float)
        ts.index = pd.DatetimeIndex(pd.to_datetime(ts.index))
        r = max([x for x in ts.index if x <= pd.to_datetime(d)])

        t0 = ts.index[0]  # this is when the data starts
        unc_cov = np.log(ts).diff(h).cov() * (252 / h)  # this is the unconditional covariance matrix annualized

        # if the dataframe has less than certain amount of data, use the unconditional covariance matrix
        if (r - t0).days < cov_window:
            cov = unc_cov.copy()
        # if the ts DataFrame has at least some amount of data, use the conditional cov
        else:
            past_data = ts.shift(1).loc[:r]  # note the day lag to not use information not available in the backtesst
            if cov_type == 'expanding':
                cond_cov = np.log(past_data).diff(h).cov() * (252 / h)
            elif cov_type == 'ewma':
                # This is roughly similar to a GARCH(1, 1) model:
                cond_cov = (np.log(past_data).diff(1).ewm(halflife=halflife).cov().loc[r]) * 252
            else:
                if cov_type != 'rolling':
                    print('cov_type not recognized, assuming rolling window of %s bdays' % str(cov_window))
                cond_cov = np.log(past_data.iloc[-cov_window:]).diff(h).cov() * (252 / h)

            count_past = past_data.count()  # this counts how munch data for each series

            # take the series that do not have enough data and replace with unconditional estimates
            for x in count_past[count_past <= cov_window].index:
                cond_cov.loc[x, :] = unc_cov.loc[x, :].values
                cond_cov.loc[:, x] = unc_cov.loc[:, x].values
            cov = cond_cov.copy()

        if shrinkage_parameter >=0 and shrinkage_parameter<1:
            vols = pd.Series(index=cov.index,data=np.sqrt(np.diag(cov)))
            corr = cov.div(vols, axis=0).div(vols, axis=1)
            corr = shrinkage_parameter * corr + (1 - shrinkage_parameter) * np.eye(len(vols))
            cov  = corr.multiply(vols, axis=0).multiply(vols, axis=1).copy()

        return cov

    @staticmethod
    def static_weights(weighting_scheme, cov=None, vol_target=0.1):
        """
        This method calculates static non-negative weights for a given weighting scheme
        This method largely makes the functions in portfolio/construction.py obsolete

        Parameters
        ----------
        weighting_scheme :  this is a string that can take the following values
            'IVP' : Inverse Volatility Portfolio
            'MVR' : Minimum Variance Portfolio
            'ERC' : Equal Risk Contribution Portfolio
            'HRP' : Hierarchical Risk Parity from López de Prado (2016) in the Journal of Portfolio Management
            'EW'  : Equal weights (this is the fall back case if the string is not recognized)

        cov : a DataFrame with the covariance matrix used in all weighting schemes but equal weights
        vol_target : only used in the Equal Risk Contribution Portfolio to set the overall volatility of the portfolio

        Returns
        -------
        a Pandas series with static non-negative weights (long-only)
        """

        assert isinstance(ts, pd.DataFrame), "input 'cov' must be a pandas DataFrame"

        # Inverse Volatility Portfolio
        if weighting_scheme == 'IVP':
            # non-negative weights are set to be proportional to the inverse of the vol, adding up to one
            w = np.sqrt(np.diag(cov))
            w = 1 / w
            w = w / w.sum()
            static_weights = pd.Series(data=w, index=cov.columns)

        # Minimum Variance Portfolio
        elif weighting_scheme == 'MVR':
            # non-negative weights are set to minimize the overall portfolio variance
            n = cov.shape[0]
            port_variance = lambda x: x.dot(cov).dot(x)
            eq_cons = {'type': 'eq', 'fun': lambda w: w.sum() - 1}
            bounds = opt.Bounds(0, np.inf)
            w0 = np.ones(n) / n
            res = opt.basinhopping(port_variance, w0, minimizer_kwargs={'method': 'SLSQP',
                                                                        'constraints': eq_cons, 'bounds': bounds},
                                   T=1.0,
                                   niter=500,
                                   stepsize=0.5,
                                   interval=50,
                                   disp=False,
                                   niter_success=100)

            if not res['lowest_optimization_result']['success']:
                raise ArithmeticError('Optimization convergence failed for static MVR weighting scheme')

            static_weights = pd.Series(data=res.x, index=cov.columns)

        # Equal Risk Contribution Portfolio
        elif weighting_scheme == 'ERC':
            # non-negative weights are set to for each component to have equal risk contribution
            n = cov.shape[0]
            target_risk_contribution = np.ones(n) / n
            dist_to_target = lambda x: np.linalg.norm(x * (x @ cov / (vol_target ** 2)) - target_risk_contribution)
            port_vol = lambda x: np.sqrt(x.dot(cov).dot(x))
            eq_cons = {'type': 'eq', 'fun': lambda x: port_vol(x) - vol_target}
            bounds = opt.Bounds(0, np.inf)
            res = opt.basinhopping(dist_to_target, target_risk_contribution,
                                   minimizer_kwargs={'method': 'SLSQP', 'constraints': eq_cons, 'bounds': bounds},
                                   T=1.0,
                                   niter=500,
                                   stepsize=0.5,
                                   interval=50,
                                   disp=False,
                                   niter_success=100)
            if not res['lowest_optimization_result']['success']:
                raise ArithmeticError('Optimization convergence failed for static ERC weighting scheme')
            static_weights = pd.Series(data=res.x, index=cov.columns)

        # Hierarchical Risk Parity
        elif weighting_scheme == 'HRP':
            # Idea is from López de Prado (2016) in the Journal of Portfolio Management
            # Code is from the book Advances in Lopez de Prado(2018), Financial Machine Learning, John Wiley & Sons
            vols = np.sqrt(np.diag(cov))
            corr = cov.div(vols, axis=0).div(vols, axis=1)
            dist = np.sqrt(np.round(((1 - corr) / 2),10))
            link = sch.linkage(dist)

            # quasi diagonal
            link = link.astype(int)
            sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
            num_items = link[-1, 3]

            while sort_ix.max() >= num_items:
                sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)  # make space
                df0 = sort_ix[sort_ix >= num_items]  # find clusters
                i = df0.index
                j = df0.values - num_items
                sort_ix[i] = link[j, 0]  # item 1
                df0 = pd.Series(link[j, 1], index=i + 1)
                sort_ix = sort_ix.append(df0)  # item 2
                sort_ix = sort_ix.sort_index()  # re-sort
                sort_ix.index = range(sort_ix.shape[0])  # re-index

            sort_ix = corr.index[sort_ix.tolist()].tolist()
            static_weights = pd.Series(1, index=sort_ix)
            c_items = [sort_ix]  # initialize all items in one cluster

            while len(c_items) > 0:
                # bi-section
                c_items = [i[j:k] for i in c_items for j, k in ((0, len(i) // 2), (len(i) // 2, len(i))) if
                           len(i) > 1]

                for i in range(0, len(c_items), 2):  # parse in pairs
                    c_items0 = c_items[i]  # cluster 1
                    c_items1 = c_items[i + 1]  # cluster 2

                    # get cluster var for 0
                    cov_ = cov.loc[c_items0, c_items0]  # matrix slice
                    ivp = 1 / np.diag(cov_)
                    ivp /= ivp.sum()
                    w_ = ivp.reshape(-1, 1)
                    c_var0 = np.dot(np.dot(w_.T, cov_), w_)[0, 0]

                    # get cluster var for 1
                    cov_ = cov.loc[c_items1, c_items1]  # matrix slice
                    ivp = 1 / np.diag(cov_)
                    ivp /= ivp.sum()
                    w_ = ivp.reshape(-1, 1)
                    c_var1 = np.dot(np.dot(w_.T, cov_), w_)[0, 0]

                    alpha = 1 - c_var0 / (c_var0 + c_var1)
                    static_weights[c_items0] *= alpha  # weight 1
                    static_weights[c_items1] *= 1 - alpha  # weight 2
        else:
            # Equal Weights
            if weighting_scheme != 'EW':
                print('%s weighting scheme is not recognized, defaulting to static equal weights' % weighting_scheme)
            n = cov.shape[0]
            static_weights = pd.Series(index=cov.index, data=1 / n)

        return static_weights

    @staticmethod
    def cross_sectional_weights_from_signals(signals, weighting_scheme = 'rank', cov = None, vol_target = 0.1):
        """
        This method calculates static long-short weights for a given set of signals

        Parameters
        ----------

        signals : a Pandas series containing a set of signals on which assets will be sorted. Typically, we want to
                  be long and have higher weight on assets with large signals and to be short and have large negative
                  weights in the assets with low signals

        weighting_scheme :  this is a string that can take the following values
            'zscores' : z-score long-short weights adding up to 200% in absolute value
            'winsorized' : same as 'zscores' but with z-scores winsorized at 10th/90th percentile limits
            'vol_target' : long-short weights set to achieve a certain volatility target for the entire portfolio
            'ERC' : Equal Risk Contribution Portfolio
            'IVP' : Inverse Volatility Portfolio
            'EW' : Equal Weights
            'rank' : Signal Rank Based Portfolio (this is the case if the parameter is not given or not recognized)

        cov : a DataFrame with the covariance matrix used in all weighting schemes but equal weights
        vol_target : used in the 'vol_target' and 'ERC' weighting schemes to set the overall volatility of the portfolio

        Returns
        -------
        a Pandas series with static long-short weights as type float
        """

        assert isinstance(signals, pd.Series), "input 'signals' must be a pandas Series"
        assert isinstance(weighting_scheme, str), "input 'weighting_scheme' must be a string"

        if weighting_scheme.lower().find('zscores')>-1:
            # z-score long-short weights adding up to 200% in absolute value
            weights = signals.copy().fillna(0) * 0
            scores = pd.Series(index=signals.dropna().index, data=stats.zscore(signals.dropna()))
            weights[scores.index] = scores.values
            weights = weights / (np.nansum(np.abs(weights)) / 2)

        elif weighting_scheme.lower().find('winsorized')>-1:
            # z-scores winsorized at 10th/90th percentile limits long-short weights adding up to 200%
            weights = signals.copy().fillna(0) * 0
            raw_scores = stats.zscore(signals.dropna())
            w_scores = stats.mstats.winsorize(raw_scores, limits=.1)
            scores = pd.Series(index=signals.dropna().index, data=w_scores)
            weights[scores.index] = scores.values
            weights = weights / (np.nansum(np.abs(weights)) / 2)

        elif weighting_scheme.lower().find('vol_target')>-1:
            # long-short weights set to achieve a certain volatility target for the entire portfolio

            # maximize the portfolio signal (actually minimize the opposite of that)
            port_signal = lambda x: - x.dot(signals.values)

            # subject to the portfolio volatility being equal to vol_target
            port_vol = lambda x: np.sqrt(x.dot(cov).dot(x)) - vol_target
            eq_cons = {'type': 'eq', 'fun': lambda x: port_vol(x)}

            # initialize optimization with rank-based portfolio
            ranks = signals.rank()
            w0 = ranks - ranks.mean()
            w0 = w0 / (np.nansum(np.abs(w0)) / 2)

            # bounds are set in order to be long/short what the rank based portfolio tells us to be long/short
            # the maximum weight in absolute value is the maximum weight in the rank-based portfolio
            bounds = pd.DataFrame(index=signals.index, columns=['lower', 'upper'])
            bounds['lower'] = np.array([np.sign(w0) * max(np.abs(w0)), np.zeros(w0.shape)]).min(axis=0)
            bounds['upper'] = np.array([np.sign(w0) * max(np.abs(w0)), np.zeros(w0.shape)]).max(axis=0)

            res = opt.basinhopping(port_signal, np.nan_to_num(w0.values),
                        minimizer_kwargs={'method': 'SLSQP', 'constraints': eq_cons, 'bounds': bounds.values},
                                   T=1.0,
                                   niter=500,
                                   stepsize=0.5,
                                   interval=50,
                                   disp=False,
                                   niter_success=100)

            if not res['lowest_optimization_result']['success']:
                raise ArithmeticError('Optimization convergence failed for volatility target weighting scheme')

            weights = pd.Series(index=signals.index, data = np.nan_to_num(res.x))

        elif weighting_scheme.find('ERC')>-1:
            # Equal Risk Contribution Portfolio

            # minimize the distance to the equal risk portfolio
            n = cov.shape[0]
            target_risk_contribution = np.ones(n) / n
            dist_to_target = lambda x: np.linalg.norm(x * (x @ cov / (vol_target ** 2)) - target_risk_contribution)

            # subject to the portfolio volatility being equal to vol_target
            port_vol = lambda x: np.sqrt(x.dot(cov).dot(x))
            eq_cons = {'type': 'eq', 'fun': lambda x: port_vol(x) - vol_target}

            # initialize optimization with rank-based portfolio
            ranks = signals.rank()
            w0 = ranks - ranks.mean()
            w0 = w0 / (np.nansum(np.abs(w0)) / 2)

            # bounds are set in order to be long/short what the rank based portfolio tells us to be long/short
            # the maximum weight in absolute value is the maximum weight in the rank-based portfolio
            bounds = pd.DataFrame(index=signals.index, columns=['lower', 'upper'])
            bounds['lower'] = np.array([np.sign(w0) * max(np.abs(w0)), np.zeros(w0.shape)]).min(axis=0)
            bounds['upper'] = np.array([np.sign(w0) * max(np.abs(w0)), np.zeros(w0.shape)]).max(axis=0)

            res = opt.basinhopping(dist_to_target, target_risk_contribution,
                                   minimizer_kwargs={'method': 'SLSQP', 'constraints': eq_cons, 'bounds': bounds.values},
                                   T=1.0,
                                   niter=500,
                                   stepsize=0.5,
                                   interval=50,
                                   disp=False,
                                   niter_success=100)

            if not res['lowest_optimization_result']['success']:
                raise ArithmeticError('Optimization convergence failed for ERC weighting scheme')
            weights = pd.Series(index=signals.index, data=np.nan_to_num(res.x))

        elif weighting_scheme.find('IVP')>-1:
            # Inverse Volatility Portfolio
            ranks = signals.rank()
            weights = ranks - ranks.mean()
            vols = pd.Series(index=cov.index, data=np.sqrt(np.diag(cov)))
            weights = np.sign(weights) / vols
            weights = weights / (np.nansum(np.abs(weights)) / 2)

        elif weighting_scheme == 'EW':
            # Equal Weights
            ranks = signals.rank()
            weights = ranks - ranks.mean()
            weights = np.sign(weights) / signals.shape[0]
            weights = weights / (np.nansum(np.abs(weights)) / 2)

        else:
            # Signal Rank Based Portfolio
            if weighting_scheme.lower().find('rank')== -1:
                print('Unclear weighting scheme, assuming signal-rank based weights')
            ranks = signals.rank()
            weights = ranks - ranks.mean()
            weights = weights / (np.nansum(np.abs(weights)) / 2)

        return weights.astype(float)

class FHLongOnlyWeights(object):
    """
    Implements long-only portfolio strategies

    Attributes
    ----------

    underlyings : a list or index with the name of the underlyings of the strategy

    ts : a Pandas DataFrame containing the indexed time series of returns for a set of underlying trackers

    rebalance_dates : DatetimeIndex with the rebalancing dates of the strategy

    weights : a Pandas DataFrame containing the time series of notional allocation (weights) on each underlying tracker
              for each rebalancing date

    holdings : a Pandas DataFrame containing the time series of the quantitiy held
               on each underlying tracker on all dates

    pnl : a Pandas Series containing the time series of the daily pnl of the strategy

    backtest : a Pandas Series containing the time series of the indexed cumulative pnl of the strategy


    Methods
    ----------

    _rescale_weights : rescale the weights to achieve a certain objective when new assets come into the portfolio.
                        Current options are:
                           'to_one' : rescale weights add to one
                           'vol' : rescale weights to meet a certain volatility target
                           'notional' :  weights are rescaled but keep the same notional as before

    run_backtest : runs the strategy, calculating the performance and the attributes backtest, pnl and holdings
                   It also returns the backtest as a Pandas DataFrame

    """


    def __init__(self, ts, DTINI='1997-12-31', DTEND='today', static = True,
                       weighting_scheme = 'IVP', rebalance='M', rescale_weights = False, vol_target = 0.1,
                       cov_type='rolling', cov_period=21, cov_window=756, halflife=60):
        """
        This class implements long-only portfolio strategies.

        Parameters
        ----------

        ts : a Pandas DataFrame containing the indexed time series of returns for a set of trackers.
             The time series do not need to start or end all at the same time and the code deals with missing data

        DTINI : a string containing the initial date for the backtest (default is '1997-12-31')

        DTEND : a string containing the end date for the backtest (default is 'today')

        static : a Boolean where True is if the strategy has static weights (default) and False otherwise

        weighting_scheme :  a string that defines the strategy weighting scheme to be used as argument on
                            the static_weights method in the FHBacktestAncilliaryFunctions class.
                            See FHBacktestAncilliaryFunctions.static_weights for different weighting scheme options.
                            Inverse Volatility Portfolio is the default weighting scheme.

        rebalance : a string, list or DatetimeIndex that defines the rebalancing frequency of the strategy.
                    The string is used as argument on the resample_dates method in the FHBacktestAncilliaryFunctions
                    class. See FHBacktestAncilliaryFunctions.resample_dates for rebalancing options
                    Month-end rebalancing is the default rebalancing scheme.

        rescale_weights : a Boolean or string that is used as an argument in the _rescale_weights method.
                          If True, or not recognized, the weights will be rescaled to add up to one when
                          new underlyings come into the portfolio.
                          Other options are described above in the _rescale_weights method description

        vol_target : a float used in some weighting schemes to set the overall volatility of the portfolio

        cov_type : is a string with the type of covariance calulation. See the cov_type parameter on the
                    get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class.
                    The default is 'rolling'

        cov_period : an integer used to calculate the rolling returns that will be used in the covariance calculation.
                     See the h parameter on the get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class.
                     The default is 21 business days, so 1 month of rolling returns

        cov_window : an integer used to determine how far back in history to calculate the rolling returns that
                     will be used in the covariance calculation. See the cov_window parameter on the
                     get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class
                     The default is 756 business days, so 3 years of data

        halflife : for cov_type equal to 'ewma' a halflife paramter may be specified. See the cov_window parameter
                   on the get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class.
                   The default is 60 bdays, about 3 months, if no parameter is specified
        """

        assert isinstance(ts, pd.DataFrame), "input 'ts' must be a pandas DataFrame"
        assert isinstance(rescale_weights, bool) or isinstance(rescale_weights, str),\
                                "input 'rescale_weights' must be boolean or string"


        # store the names of the underlyings
        self.underlyings = ts.columns

        # fill na's and store time series data
        ts = ts.copy().fillna(method='ffill').dropna(how='all')
        ts.index = pd.DatetimeIndex(pd.to_datetime(ts.index))
        relevant_time_period = pd.DatetimeIndex([t for t in ts.index if
                                                 pd.to_datetime(DTINI) <= t <= pd.to_datetime(DTEND)])
        self.ts = ts.loc[relevant_time_period]

        # find and store the rebalancing dates
        baf = FHBacktestAncilliaryFunctions()
        self.rebalance_dates = baf.resample_dates(relevant_time_period, rebalance)

        # find weights
        if static: # static weights case, so same weights every rebalance date
                try:
                    cov = baf.get_cov_matrix_on_date(ts.dropna().index[-1], ts, h=cov_period,
                                        cov_type='expanding', cov_window=cov_window, halflife=halflife)
                    static_weights = baf.static_weights(weighting_scheme, cov, vol_target=vol_target)
                except: # fall back to equal weights if weighting_scheme parameters is not recognized
                    print('%s weighting scheme is not recognized, defaulting to static equal weights' % weighting_scheme)
                    weighting_scheme = 'EW'
                    static_weights = baf.static_weights(weighting_scheme)
                self.weights = baf.expand_static_weights(self.rebalance_dates, static_weights)

        else:
            dynamic_weights = pd.DataFrame(index=self.rebalance_dates,columns=ts.columns)
            for r in dynamic_weights.index:
                cov = baf.get_cov_matrix_on_date(r, ts, cov_type=cov_type, h=cov_period,
                                                 cov_window=cov_window, halflife=halflife)
                static_weights = baf.static_weights(weighting_scheme, cov, vol_target=vol_target)
                dynamic_weights.loc[r] = static_weights.values
            self.weights = dynamic_weights.copy()


        # default to one if rescale_weights = True
        rsw_string = 'to_one' if isinstance(rescale_weights, bool) and rescale_weights else rescale_weights

        if rsw_string and static:
            # if raw_string is True or a string, this will be true
            # also, only makes sense to re-scale static weights, dynamic weights are already rescaled
            if rescale_weights == True: # only print this if boolean True
                print('type of re-scaling not given, rescalling to one')
            self._rescale_weights(by=rsw_string, vol_target=vol_target, cov_type=cov_type,
                                  h=cov_period, cov_window=cov_window, halflife=halflife)

    def _rescale_weights(self, by='to_one', vol_target=0.1, h=21, cov_type='rolling', cov_window=756, halflife=60):
        """"
        This function transforms static weights in a dataframe of constant weights having dates_to_expand as index

        Parameters
        ----------

        by : method by which weights are supposed to be re-scaled
                'to_one' : rescale weights add to one
                'vol' : rescale weights to meet a certain volatility target
                'notional' :  weights are rescaled but keep the same notional as before

        for other parameters see get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class
        """

        r_weights = (self.ts.reindex(self.weights.index).notnull()*self.weights).copy()
        if by == 'notional':
            notional = self.weights.dropna().iloc[-1].sum()
            k = notional / r_weights.sum(axis=1)
            r_weights = r_weights.fillna(0).multiply(k,axis=0)
        elif by == 'vol':
            num_assets_in_reb_date = self.ts.reindex(self.weights.index).dropna(how='all').count(axis=1)
            for r in num_assets_in_reb_date.index:
                if num_assets_in_reb_date.diff(1).loc[r] != 0:
                    active_assets = r_weights.loc[r][r_weights.loc[r] != 0].index
                    cov = FHBacktestAncilliaryFunctions.get_cov_matrix_on_date(r, self.ts[active_assets],
                                                h=h, cov_type=cov_type, cov_window=cov_window, halflife=halflife)
                    rescale_factor = vol_target / np.sqrt((r_weights.loc[r,active_assets] @ cov) @ r_weights.loc[r,active_assets])
                    r_weights.loc[r] = rescale_factor * r_weights.loc[r]
                else:
                    r_weights.loc[r] = r_weights.loc[:r].iloc[-2].values
        else:
            if by != 'to_one':
                print('type of re-scaling not recognized, rescalling to one')
            k = 1 / r_weights.sum(axis=1)
            r_weights = r_weights.fillna(0).multiply(k,axis=0)
        self.weights = r_weights.copy().fillna(method='ffill').dropna(how='all')


    def run_backtest(self, backtest_name = 'backtest'):
        """"
        Runs the strategy, calculating the performance and the attributes backtest, pnl and holdings

        The resulting single-column Pandas DataFrame with the backtest will be stored in the backtest attribute
        with backtest_name as sole column name

        """
        # TODO: incorporate transaction costs

        # set up backtest series. Same calendar as the underlying time series and indexed to start at one
        self.backtest = pd.Series(index=self.ts.index)
        self.backtest.iloc[0] = 1

        # set up pnl series. Same calendar as the underlying time series and indexed to start at zero pnl on day one
        self.pnl = pd.Series(index=self.ts.index)
        self.pnl.iloc[0] = 0

        # take the first set of weights available and use those at the start of the backtest
        if min(self.weights.index)>min(self.ts.index):
            w0 = pd.DataFrame(columns=[min(self.ts.index)], index=self.weights.columns, data=self.weights.iloc[0].values)
            self.weights = self.weights.append(w0.T).sort_index()

        # set up the DataFrame that will store the quantities of each underlying held during the backtest
        self.holdings = pd.DataFrame(index=self.ts.index,columns=self.ts.columns)
        self.holdings.iloc[0] = self.weights.iloc[0] / self.ts.iloc[0] # first trade

        # loop over days, running the strategy
        for t, tm1 in zip(self.backtest.index[1:], self.backtest.index[:-1]):

            # calculate pnl as q x change in price
            prices_t = self.ts.loc[:t].iloc[-1]
            previous_prices = self.ts.loc[:tm1].iloc[-1]
            self.pnl[t] = (self.holdings.loc[tm1].copy() * (prices_t -previous_prices)).sum()

            # acumulate the pnl in the backtest series
            self.backtest[t] = self.backtest[tm1] + self.pnl[t]

            # check if it is a rebalancing day, if so, recalculate the holdings based on new weights, i.e., rebalance
            if t in self.weights.index:
                self.holdings.loc[t] = self.backtest.loc[tm1]*self.weights.loc[t] / self.ts.loc[t]
            else:
                self.holdings.loc[t] = self.holdings.loc[tm1].copy()

        self.backtest = self.backtest.astype(float).to_frame(backtest_name).copy()
        return self.backtest

class FHSignalBasedWeights(object):
    """
    Implements long-short portfolio strategies

    Attributes
    ----------

    underlyings : a list or index with the name of the underlyings of the strategy

    ts : a Pandas DataFrame containing the indexed time series of returns for a set of underlying trackers

    rebalance_dates : DatetimeIndex with the rebalancing dates of the strategy

    weights : a Pandas DataFrame containing the time series of notional allocation (weights) on each underlying tracker
              for each rebalancing date

    holdings : a Pandas DataFrame containing the time series of the quantitiy held
               on each underlying tracker on all dates

    traded_notional : a Pandas DataFrame containing the notional traded on each underlying on each date of the strategy

    pnl : a Pandas Series containing the time series of the daily pnl of the strategy

    backtest : a Pandas Series containing the time series of the indexed cumulative pnl of the strategy


    Methods
    ----------

    run_backtest : runs the strategy, calculating the performance and the attributes backtest, pnl and holdings
                   It also returns the backtest as a Pandas DataFrame

    """

    def __init__(self, ts, signals, DTINI='1997-12-31', DTEND='today',
                 weighting_scheme = 'IVP', rebalance='M', vol_target = 0.1,
                 cov_type='rolling', cov_period=21, cov_window=756, halflife=60):
        """
        This class implements long-short portfolio strategies.

        Parameters
        ----------

        ts : a Pandas DataFrame containing the indexed time series of returns for a set of trackers.
             The time series do not need to start or end all at the same time and the code deals with missing data

        signals : a Pandas DataFrame containing the time series of the signals used to go long or short each underlying
                  The time series do not need to start or end all at the same time and the code deals with missing data

        DTINI : a string containing the initial date for the backtest (default is '1997-12-31')

        DTEND : a string containing the end date for the backtest (default is 'today')

        weighting_scheme :  a string that defines the strategy weighting scheme to be used as argument on
                            the cross_sectional_weights_from_signals method in the FHBacktestAncilliaryFunctions class.
                            See FHBacktestAncilliaryFunctions.cross_sectional_weights_from_signals for different
                            weighting scheme options.

        rebalance : a string, list or DatetimeIndex that defines the rebalancing frequency of the strategy.
                    The string is used as argument on the resample_dates method in the FHBacktestAncilliaryFunctions
                    class. See FHBacktestAncilliaryFunctions.resample_dates for rebalancing options
                    Month-end rebalancing is the default rebalancing scheme.

        vol_target : a float used in some weighting schemes to set the overall volatility of the portfolio

        cov_type : is a string with the type of covariance calulation. See the cov_type parameter on the
                    get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class.
                    The default is 'rolling'

        cov_period : an integer used to calculate the rolling returns that will be used in the covariance calculation.
                     See the h parameter on the get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class.
                     The default is 21 business days, so 1 month of rolling returns

        cov_window : an integer used to determine how far back in history to calculate the rolling returns that
                     will be used in the covariance calculation. See the cov_window parameter on the
                     get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class
                     The default is 756 business days, so 3 years of data

        halflife : for cov_type equal to 'ewma' a halflife paramter may be specified. See the cov_window parameter
                   on the get_cov_matrix_on_date method of the FHBacktestAncilliaryFunctions class.
                   The default is 60 bdays, about 3 months, if no parameter is specified
        """

        assert isinstance(ts, pd.DataFrame), "input 'ts' must be a pandas DataFrame"
        assert isinstance(signals, pd.DataFrame), "input 'signals' must be a pandas DataFrame"

        # store the names of the underlyings
        self.underlyings = pd.Index([x for x in ts.columns if x in signals.columns])

        # fill na's and store time series data
        ts = ts.copy().fillna(method='ffill').dropna(how='all')
        ts.index = pd.DatetimeIndex(pd.to_datetime(ts.index))
        t0 = max(signals.index.min(),pd.to_datetime(DTINI))
        relevant_time_period = pd.DatetimeIndex([t for t in ts.index if t0 <= t <= pd.to_datetime(DTEND)])
        self.ts = ts.loc[relevant_time_period,self.underlyings]

        # find and store the rebalancing dates
        baf = FHBacktestAncilliaryFunctions()
        self.rebalance_dates = baf.resample_dates(relevant_time_period, rebalance)

        # get weights according to given weighting scheme
        dynamic_weights = pd.DataFrame(index=self.rebalance_dates, columns=self.underlyings)
        for r in dynamic_weights.index:
            if weighting_scheme in ['vol_target','ERC','IVP']:
                cov = baf.get_cov_matrix_on_date(r, ts, h=cov_period, cov_type=cov_type,
                                                                cov_window=cov_window, halflife=halflife)
            else:
                cov = None
            static_weights = baf.cross_sectional_weights_from_signals(signals.loc[r],
                                                                      weighting_scheme=weighting_scheme,
                                                                      cov=cov, vol_target=vol_target)
            dynamic_weights.loc[r] = static_weights.values
        self.weights = dynamic_weights.copy()

    def run_backtest(self, backtest_name = 'backtest', holdings_costs_bps_pa = 0, rebalance_costs_bps = 0):
        """"
        Runs the strategy, calculating the performance and the attributes backtest, pnl and holdings

        Parameters
        ----------

        backtest_name : a string. The resulting single-column Pandas DataFrame with the backtest will be stored in the backtest attribute
        with backtest_name as sole column name

        holdings_costs_bps_pa : a Pandas Series with the cost per year in bps of holding 100% notional of each underlying
                                if a float or an integer is given, that number will be used for all underlyings
                                Default is zero holdings costs

        rebalance_costs_bps : a Pandas Series with the cost of trading in/out of 100% notional of each underlying
                              if a float or an integer is given, that number will be used for all underlyings
                              Default is zero holdings costs

        """

        # set up backtest series. Same calendar as the underlying time series and indexed to start at one
        self.backtest = pd.Series(index=self.ts.index)
        self.backtest.iloc[0] = 1

        # set up pnl series. Same calendar as the underlying time series and indexed to start at zero pnl on day one
        self.pnl = pd.Series(index=self.ts.index)
        self.pnl.iloc[0] = 0

        # take the first set of weights available and use those at the start of the backtest
        if min(self.weights.index)>min(self.ts.index):
            w0 = pd.DataFrame(columns=[min(self.ts.index)], index=self.weights.columns, data=self.weights.iloc[0].values)
            self.weights = self.weights.append(w0.T).sort_index()

        # set up the DataFrame that will store the quantities of each underlying held during the backtest
        self.holdings = pd.DataFrame(index=self.ts.index,columns=self.ts.columns)
        self.holdings.iloc[0] = self.weights.iloc[0] / self.ts.iloc[0]

        # set up the DataFrame that will store the traded notionals of each underlying per day
        self.traded_notional = pd.DataFrame(index=self.ts.index,columns=self.ts.columns,data=0)


        # set up the tc Series that will keep the rebalancing costs
        if isinstance(rebalance_costs_bps, pd.Series):
            tc = rebalance_costs_bps[self.ts.columns] / 10000
        elif isinstance(rebalance_costs_bps, float) or isinstance(rebalance_costs_bps, int):
            tc = pd.Series(index=self.ts.columns,data=rebalance_costs_bps/10000)
        else:
            tc = pd.Series(index=self.ts.columns, data=0)

        # set up the hc Series that will keep the holding costs
        if isinstance(holdings_costs_bps_pa, pd.Series):
            hc = holdings_costs_bps_pa[self.ts.columns] / 10000
        elif isinstance(holdings_costs_bps_pa, float) or isinstance(holdings_costs_bps_pa, int):
            hc = pd.Series(index=self.ts.columns, data=holdings_costs_bps_pa / 10000)
        else:
            hc = pd.Series(index=self.ts.columns, data=0)

        reb_costs = 0

        # loop over days, running the strategy
        for t, tm1 in zip(self.backtest.index[1:], self.backtest.index[:-1]):

            # calculate pnl as q x change in price
            prices_t = self.ts.loc[:t].iloc[-1]
            previous_prices = self.ts.loc[:tm1].iloc[-1]
            self.pnl[t] = (self.holdings.loc[tm1] * (prices_t -previous_prices)).sum()

            # take out holdings costs from the pnl
            holdings_costs = (self.holdings.loc[tm1] * previous_prices * hc * (t - tm1).days/365.25).sum()

            # acumulate the net of transaction costs pnl in the backtest series
            self.backtest[t] = self.backtest[tm1] + self.pnl[t] - reb_costs - holdings_costs
            reb_costs = 0

            if t in self.weights.index: # if it is a rebalance date
                # recalculate the notionals based on the new weights, i.e., rebalance
                self.holdings.loc[t,:] = (self.backtest.loc[tm1]*self.weights.loc[t] / self.ts.loc[t]).values

                # calcualte the trasaction costs to be subtracted from the next day pnl
                self.traded_notional.loc[t,:] = (np.abs(self.holdings.loc[t] - self.backtest.loc[tm1])* prices_t).values
                reb_costs = (self.traded_notional.loc[t,:] * tc).sum()
            else:
                self.holdings.loc[t] = self.holdings.loc[tm1].copy()


        self.backtest = self.backtest.astype(float).to_frame(backtest_name).copy()
        return self.backtest










