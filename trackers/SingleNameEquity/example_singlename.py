from trackers import SingleNameEquity
import matplotlib.pyplot as plt

sne = SingleNameEquity('KO UN Equity')

sne.ts_df[['Dividend']].plot()
plt.show()

sne.ts_df[['Quantity']].plot()
plt.show()

sne.ts_df[['Price', 'Total Return Index']].plot()
plt.show()

sne.ts_df[['Price', 'Total Return Index']].pct_change(1).plot()
plt.show()


