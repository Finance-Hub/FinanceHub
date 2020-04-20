import pandas as pd
import numpy as np


class Performance(object):
    @staticmethod
    def expanding_dd(ser):
        max2here = ser.expanding(min_periods=1).max()
        dd2here = ser/max2here - 1.0
        return dd2here

    def max_dd(self, ser):
        dd2here = self.expanding_dd(ser)
        return dd2here.min()

    def get_perf_table_single(self, index_ts, index_name='perf_table', freq='daily'):
        if type(index_ts) == pd.core.series.Series:
            clean_index_series = index_ts.copy()
        else:
            index_name = index_ts.columns[0]
            clean_index_series = index_ts[index_name].copy()

        adju_factor = 252.0
        if freq == 'monthly':
            adju_factor = 12.0
        elif freq == 'weekly':
            adju_factor = 52.0

        table = pd.Series()
        table['frequency'] = freq
        table['excess_returns'] = (clean_index_series[-1]/clean_index_series[0]) ** \
                                  (adju_factor/(len(clean_index_series)-1.0))-1

        log_returns = np.log(clean_index_series).diff(1).dropna()
        table['volatility'] = log_returns.std()*np.sqrt(adju_factor)
        table['sharpe'] = table['excess_returns']/table['volatility']
        table['sortino'] = table['excess_returns']/(np.sqrt(adju_factor)*(log_returns[log_returns<0.0]).std())

        table['maxDD'] = self.max_dd(clean_index_series)
        table['maxDD_to_vol_ratio'] = self.max_dd(clean_index_series)/table['volatility']

        table['from_date'] = clean_index_series.index[0].strftime('%d-%b-%y')
        table['to_date'] = clean_index_series.index[-1].strftime('%d-%b-%y')
        table['n_obs'] = len(clean_index_series)

        return table.to_frame(index_name)

    def get_perf_table(self, index_ts, freq='daily', same_window=True):
        if type(index_ts) == pd.core.series.Series:
            return self.get_perf_table_single(index_ts.dropna().sort_index(), freq=freq)
        else:
            if len(index_ts.columns) == 1:
                return self.get_perf_table_single(index_ts.dropna().sort_index(), freq=freq)
            else:
                if same_window:
                    index_ts = index_ts.dropna()
                tables = pd.DataFrame()
                for case in index_ts.columns:
                    case_pt = self.get_perf_table_single(index_ts[case].dropna().sort_index(), index_name=case, freq=freq)
                    tables = pd.concat([tables,case_pt],axis=1)
                return tables

    @staticmethod
    def get_3T_sharpe_stats_single(index_ts, index_name='sharpe_over_3_periods', freq='daily'):
        if type(index_ts) == pd.core.series.Series:
            clean_index_series = index_ts.copy()
        else:
            index_name = index_ts.columns[0]
            clean_index_series = index_ts[index_name].copy()

        adju_factor = 252.0
        if freq == 'monthly':
            adju_factor = 12.0
        elif freq == 'weekly':
            adju_factor = 52.0

        returns_3T = (1. + clean_index_series.pct_change(int(adju_factor * 3.))) ** (1. / 3.) - 1.
        vol_3T = np.log(clean_index_series).diff(1).rolling(window=int(adju_factor * 3.)).std() * np.sqrt(adju_factor)
        hist_3T_sharpe = ((returns_3T / vol_3T).dropna()).describe()
        hist_3T_sharpe['freq'] = freq
        hist_3T_sharpe['from_date'] = returns_3T.index[0].strftime('%d-%b-%y')
        hist_3T_sharpe['to_date'] = returns_3T.index[-1].strftime('%d-%b-%y')

        return hist_3T_sharpe.to_frame(index_name)

    def get_3T_sharpe_stats(self,index_ts, freq='daily',same_window=True):
        if type(index_ts) == pd.core.series.Series:
            return self.get_3T_sharpe_stats_single(index_ts.dropna().sort_index(), freq=freq)
        else:
            if len(index_ts.columns)==1:
                return self.get_3T_sharpe_stats_single(index_ts.dropna().sort_index(), freq=freq)
            else:
                if same_window:
                    index_ts = index_ts.dropna()
                tables = pd.DataFrame()
                for case in index_ts.columns:
                    case_pt = self.get_3T_sharpe_stats_single(index_ts[case].dropna().sort_index(), index_name=case, freq=freq)
                    tables = pd.concat([tables,case_pt],axis=1)
                return tables

    @staticmethod
    def get_yearly_sharpe_single(index_ts, index_name = 'yearly_sharpe'):
        if type(index_ts) == pd.core.series.Series:
            clean_index_series = index_ts.copy()
        else:
            index_name = index_ts.columns[0]
            clean_index_series = index_ts[index_name].copy()

        returns = clean_index_series.resample('M').last().pct_change(1).dropna()

        yearly_sharpe = pd.Series(index=sorted(list(set([d.year for d in returns.index]))))
        for year in yearly_sharpe.index:
            year_calendar = [d for d in returns.index if d.year == year]
            ret = (1.+returns.loc[year_calendar]).product()**(12./len(year_calendar))-1.
            vol = returns.loc[year_calendar].std() * np.sqrt(12.)
            yearly_sharpe[year] = ret/vol

        return yearly_sharpe.to_frame(index_name)

    def get_yearly_sharpe(self,index_ts, same_window=True):
        if type(index_ts) == pd.core.series.Series:
            return self.get_yearly_sharpe_single(index_ts.dropna().sort_index())
        else:
            if len(index_ts.columns)==1:
                return self.get_yearly_sharpe_single(index_ts.dropna().sort_index())
            else:
                if same_window:
                    index_ts = index_ts.dropna()
                tables = pd.DataFrame()
                for case in index_ts.columns:
                    case_pt = self.get_yearly_sharpe_single(index_ts[case].dropna().sort_index(), index_name=case)
                    tables = pd.concat([tables,case_pt],axis=1)
                return tables

    @staticmethod
    def get_monthly_return_table_single(index_ts, index_name='perf_table'):
        if type(index_ts) == pd.core.series.Series:
            clean_index_series = index_ts.copy()
        else:
            index_name = index_ts.columns[0]
            clean_index_series = index_ts[index_name].copy()

        returns = clean_index_series.resample('M').last().pct_change(1).dropna()

        table = pd.DataFrame(index=sorted(list(set([d.year for d in returns.index]))),
                             columns=sorted(list(set([d.month for d in returns.index]))))
        yearly_sharpe = pd.DataFrame(index=sorted(list(set([d.year for d in returns.index]))),
                                     columns=['ret','vol'])

        for d in returns.index:
            table.loc[d.year, d.month] = returns[d]

        for year in yearly_sharpe.index:

            year_calendar = [d for d in returns.index if d.year == year]
            yearly_sharpe.loc[year,'ret'] = (1.+returns.loc[year_calendar]).product()**(12./len(year_calendar))-1.
            yearly_sharpe.loc[year, 'vol'] = returns.loc[year_calendar].std() * np.sqrt(12.)

        yearly_sharpe['sharpe'] = yearly_sharpe['ret']/yearly_sharpe['vol']

        df = pd.concat([table, yearly_sharpe], axis=1)
        df.index.name = index_name

        return df

    @staticmethod
    def get_qq_table_single(index_ts, ref_index, metric='mean', index_name='quintiles'):
        if type(index_ts) == pd.core.series.Series:
            clean_index_series = index_ts.copy()
        else:
            index_name = index_ts.columns[0]
            clean_index_series = index_ts[index_name].copy()

        if type(ref_index) == pd.core.series.Series:
            clean_ref_index_series = ref_index.copy()
        else:
            index_name = ref_index.columns[0]
            clean_ref_index_series = ref_index[index_name].copy()

        df = pd.concat([clean_ref_index_series,clean_index_series],join='outer',axis=1).fillna(method='ffill')
        ret = df.pct_change(1).dropna()

        if metric == 'mean':
            my_function = lambda x: x.mean()
        elif metric == 'median':
            my_function = lambda x: x.median()
        elif metric == 'sharpe':
            my_function = lambda x: x.mean()/x.std()
        elif metric == 'q1':
            my_function = lambda x: x.quantile(q=.25)
        elif metric == 'q3':
            my_function = lambda x: x.quantile(q=.75)
        elif metric == 'p10':
            my_function = lambda x: x.quantile(q=.10)
        elif metric == 'p90':
            my_function = lambda x: x.quantile(q=.90)

        q1 = ret.iloc[:, 0].quantile(q=.2)
        q2 = ret.iloc[:, 0].quantile(q=.4)
        q3 = ret.iloc[:, 0].quantile(q=.6)
        q4 = ret.iloc[:, 0].quantile(q=.8)

        quintis = pd.Series(index=['q1', 'q2', 'q3', 'q4', 'q5'])

        quintis['q1'] = my_function(ret[ret.iloc[:, 0] <= q1].iloc[:, 1])
        quintis['q2'] = my_function(ret[q1 <= ret.iloc[:, 0]][ret.iloc[:, 0] <= q2].iloc[:, 1])
        quintis['q3'] = my_function(ret[q2 <= ret.iloc[:, 0]][ret.iloc[:, 0] <= q3].iloc[:, 1])
        quintis['q4'] = my_function(ret[q3 <= ret.iloc[:, 0]][ret.iloc[:, 0] <= q4].iloc[:, 1])
        quintis['q5'] = my_function(ret[q4 <= ret.iloc[:, 0]].iloc[:, 1])
        quintis['from_date'] = df.index[0].strftime('%d-%b-%y')
        quintis['to_date'] = df.index[-1].strftime('%d-%b-%y')

        return quintis.to_frame(index_name)

    # INCOMPLETE
    # def compare_charts(x_df):
    #     local_df = (np.exp(np.log(x_df).diff(1).cumsum())).copy()
    #     local_df.plot(title='backtests')
    #     plt.show()
    #
    #     (local_df.iloc[:,0]/local_df.iloc[:,1]).dropna().plot()
    #     plt.title('Ratio: %s / %s' % (local_df.columns[0],local_df.columns[1]))
    #     plt.show()
    #
    #     plt.scatter(local_df.pct_change(1).dropna().iloc[:,0],local_df.pct_change(1).dropna().iloc[:,1])
    #     plt.title('Daily returns scatter plot')
    #     plt.xlabel(local_df.columns[0])
    #     plt.ylabel(local_df.columns[1])
    #     plt.show()
    #
    #     (np.log(local_df).diff(1).rolling(window=3*252,min_periods=3*252).std()*np.sqrt(252)).plot()
    #     plt.title('Rolling 3y volatility')
    #     plt.show()

    # INCOMPLETE
    # def get_monthly_return_table(self,index_ts, same_window=True):
    #     if type(index_ts) == pd.core.series.Series:
    #         return self.get_monthly_return_table_single(index_ts.dropna().sort_index())
    #     else:
    #         if len(index_ts.columns)==1:
    #             return self.get_monthly_return_table_single(index_ts.dropna().sort_index())
    #         else:
    #             if same_window:
    #                 index_ts = index_ts.dropna()
    #             tables = pd.DataFrame()
    #             for case in index_ts.columns:
    #                 case_pt = self.get_monthly_return_table_single(index_ts[case].dropna().sort_index(), index_name=case)
    #                 tables = pd.concat([tables,case_pt],axis=1)
    #             return tables