from trackers import SingleNameEquity
import matplotlib.pyplot as plt

sne = SingleNameEquity('ITUB4 BZ Equity')

sne.df_ts[['Dividend']].plot()
plt.show()

sne.df_ts[['Quantity']].plot()
plt.show()

sne.df_ts[['Price', 'Total Return Index']].plot()
plt.show()

sne.df_ts[['Price', 'Total Return Index']].pct_change(1).plot()
plt.show()
