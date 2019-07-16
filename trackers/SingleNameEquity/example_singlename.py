from trackers import SingleNameEquity
import matplotlib.pyplot as plt

sne = SingleNameEquity('GE US Equity')

sne.df_ts[['Dividend']].plot()
plt.show()

sne.df_ts[['Quantity']].plot()
plt.show()

sne.df_ts[['Price', 'Total Return Index']].plot()
plt.show()

sne.df_ts[['Price', 'Total Return Index']].pct_change(1).plot()
plt.show()

sne.df_ts[['Price', 'Total Return Index']].pct_change(1).plot.scatter(0, 1, s=1)
plt.show()
