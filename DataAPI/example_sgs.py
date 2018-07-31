"""
This example grabs the Brazilian Seasonally Adjusted Real GDP Index from the SGS database. Its series ID is 22109
"""

from DataAPI import SGS
import matplotlib.pyplot as plt

sgs = SGS()

df_GDP = sgs.fetch(22109)

df_GDP.plot()
plt.show()
