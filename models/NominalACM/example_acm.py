from models import NominalACM
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ===== Custom Functions =====
def get_excess_returns(df):

    excess_returns = pd.DataFrame(index=df.index, columns=df.columns)

    for n in df.columns[1:]:
        p_n_minus_1_d = np.exp(-df[n - 1] * ((n - 1) / 12))
        p_n_d_minus_1 = (np.exp(-df[n] * (n / 12))).shift(1)
        ret_n_d = np.log(p_n_minus_1_d / p_n_d_minus_1)
        excess_returns[n] = ret_n_d - df[3].shift(1) * (1 / 12)

    return excess_returns


df_curve = pd.read_excel(r'US interpolated curve.xlsx', index_col='Dates')
df_exp_curve = np.log(1 + df_curve)
df_returns = get_excess_returns(df_exp_curve)
df_returns = df_returns.dropna(how='all', axis=0).dropna(how='all', axis=1)
df_curve = df_curve.reindex(index=df_returns.index)

acm = NominalACM(curve=df_curve, excess_returns=df_returns, freq='monthly')

acm.term_premium[120].plot()
plt.show()
