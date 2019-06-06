from portfolio import HRP
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def generate_data(n_obs, size0, size1, sigma1):
    x = np.random.normal(0, 1, size=(n_obs, size0))
    cols = [np.random.randint(0, size0-1) for i in range(size1)]
    y = x[:, cols] + np.random.normal(0, sigma1, size=(n_obs, len(cols)))
    x = np.append(x, y, axis=1)
    df = pd.DataFrame(data=x, columns=['r' + str(r) for r in range(1, x.shape[1] + 1)])
    return df, cols


df, cols = generate_data(100, 3, 2, 0.5)

hrp = HRP(data=df)
print(hrp.link)

# labels = list(df.columns)
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



