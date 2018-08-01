"""
This example grabs the US Seasonally Adjusted Real GDP from the FRED database. Its series ID is GDPC1
"""

from DataAPI import FRED
import matplotlib.pyplot as plt

fred = FRED()

df_GDP = fred.fetch('GDPC1')

df_GDP.plot()
plt.show()
