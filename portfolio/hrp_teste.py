from portfolio import HRP
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def generate_mnorm(n_var, n_obs):
    mu = np.zeros(n_var)
    sd = np.random.uniform(1, 3, n_var)
    corr = np.random.uniform(-1, 1, (n_var, n_var))

    for ii in range(corr.shape[0]):
        corr[ii, ii] = 1

    covar = np.diag(sd).dot(corr).dot(np.diag(sd))

    data = np.random.multivariate_normal(mu, covar, n_obs)

    df = pd.DataFrame(data=data,
                      columns=['r' + str(i) for i in range(data.shape[1])])
    return df, corr


df_simul, corr_true = generate_mnorm(5, 1000)

hrp = HRP(data=df_simul)
print(hrp.link)
print(corr_true)

# labels = list(df_simul.columns)
# plt.pcolor(hrp.corr)
# plt.colorbar()
# plt.yticks(np.arange(.5, hrp.corr.shape[0]+.5), labels)
# plt.xticks(np.arange(.5, hrp.corr.shape[0]+.5), labels)
# plt.show()


# labels = hrp.sort_ix
# plt.pcolor(hrp.sorted_corr)
# plt.colorbar()
# plt.yticks(np.arange(.5,hrp.sorted_corr.shape[0]+.5), labels)
# plt.xticks(np.arange(.5,hrp.sorted_corr.shape[0]+.5), labels)
# plt.show()

hrp.plot_corr_matrix()
hrp.plot_dendrogram()
