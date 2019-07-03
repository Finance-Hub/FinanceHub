"""
Author: Fernando Tassinari Moraes
BAB Factor Builder Routine
Paper: Frazziniand Pedersen (2014) - "Betting Against Beta"
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Preparing the data set

df = pd.read_csv(r"DataA.csv", sep=",")            # MKT + Securities Returns

df_rf = pd.read_csv(r"DataF.csv", sep=",")        # Risk Free
df_rf.index = pd.to_datetime(df_rf.Data)
df_rf = df_rf.drop("Data",axis=1)

df.index = pd.to_datetime(df.Date)
df = df.drop("Date",axis=1)

# Ex ante Beta

df_var = df.rolling(12).var()                                # 1Y Securities Variance
df_var.columns = [col + "var" for col in df_var.columns]

cols = list(df.columns)
cols.remove("MKT")
df_cov = df.MKT.rolling(60).cov(df[cols])                    # 5Y Securities Covariance with MKt
df_cov.columns = [col + "cov" for col in df_cov.columns]

df_final = pd.concat([df_cov, df_var], axis=1)
df_final = df_final.dropna(axis=0)

col_variance_names = [col + "var" for col in df.columns]
col_base_names = [col for col in df.columns]
col_base_names.remove("MKT")

betas = dict()
array_size = len(df_final[["X1var"]].values)

for var_name, base_name in zip(col_variance_names, col_base_names):
    cov = df_final[[base_name + "cov"]].values.reshape(1, array_size)
    betas[base_name] = cov * (df_final[[base_name + "var"]].values.reshape(1, array_size) / df_final.MKTvar.values.reshape(1, array_size))

df_betas = pd.DataFrame({k:v.reshape(-1,) for k,v in betas.items()})  # Securities Betas
df_betas = df_betas.set_index(df_final.index)

df_normbeta = (df_betas * 0.6) + 0.4                                 # Securities Ajusted Betas

# Ranking the Securities

df_normbeta_rank = df_normbeta.rank(axis=1)                           # Z score

z_bar = df_normbeta_rank.sum(axis=1) / len(df_normbeta_rank.columns)
z_diff = (df_normbeta_rank.transpose() - z_bar.values).transpose()
k = 2 / np.abs(z_diff).sum(axis=1)
k = k.iloc[0]                                                          # Normalized Constante

# Finding weights portfolios

def high_filter(x):
    if x > 0:
        return x
    else:
        return 0

def low_filter(x):
    if x < 0:
        return x
    else:
        return 0

weights_high = df_normbeta_rank[z_diff.apply(lambda x: x> 0)]
weights_high = weights_high.fillna(0)
weights_high = k*weights_high                                   # High Weights


weights_low = df_normbeta_rank[z_diff.apply(lambda x: x <= 0)]
weights_low = weights_low.fillna(0)
weights_low = k*weights_low                                     # Low Weights

# Finding BAB Factors

df_stocks = df.drop("MKT", axis=1)
df_stocks = df_stocks.loc[weights_low.index]

rets_low  =[]                                                  # Long Portfolio (low Beta)
rets_high =[]                                                  # Short Portfolio (high Beta)
for row_stock, row_weight_low, row_weight_high  in zip(df_stocks.iterrows(), weights_low.iterrows(), weights_high.iterrows()):
    rets_low.append(np.dot(row_stock[1], row_weight_low[1]))
    rets_high.append(np.dot(row_stock[1], row_weight_high[1]))

rets_weights = pd.DataFrame({"ret_low": rets_low, "rets_high": rets_high})

betas_low  =[]                                                 # Low Beta
betas_high =[]                                                 # High Beta
df_normbeta_hl = df_normbeta.loc[weights_low.index]
for row_stock, row_weight_low, row_weight_high  in zip(df_normbeta_hl.iterrows(), weights_low.iterrows(), weights_high.iterrows()):
    betas_low.append(np.dot(row_stock[1], row_weight_low[1]))
    betas_high.append(np.dot(row_stock[1], row_weight_high[1]))

betas_weights = pd.DataFrame({"betas_low": betas_low, "betas_high": betas_high})

risk_premium = rets_weights.values - df_rf.loc[weights_low.index].values
inverted_betalow = 1 / np.array(betas_low)
inverted_betahigh = 1 / np.array(betas_high)

final_bab = inverted_betalow * risk_premium[:,0] - inverted_betahigh * risk_premium[:, 1]   # BAB Factor
df_bab = pd.DataFrame({"ret_bab": final_bab}, index=weights_low.index)

df_bab.plot()
plt.show()
