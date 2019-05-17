from dataapi import FRED
import matplotlib.pyplot as plt

fred = FRED()

series_dict = {'INDPRO': 'Industrial Production',
               'CPILFESL': 'CPI Core Index'}

df = fred.fetch(series_dict)

df.plot()
plt.show()
