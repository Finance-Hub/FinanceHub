"""
This example grabs the US Seasonally Adjusted Industrial production and Core CPI from the FRED database using the FRED
class.
"""

from DataAPI import FRED
import matplotlib.pyplot as plt

fred = FRED()

series_dict = {'INDPRO': 'Industrial Production',
               'CPILFESL': 'CPI Core Index'}

df = fred.fetch(series_dict)

df.plot()
plt.show()
