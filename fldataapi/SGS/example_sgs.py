"""
This example grabs the Monthly proxy for the Brazilian Seasonally Adjusted Real GDP Index and monthly inflation rate
from the SGS database.
"""

from fldataapi import SGS
import matplotlib.pyplot as plt

series_dict = {24364: 'Real Monthly GDP',
               433: 'IPCA MoM'}

sgs = SGS()

df = sgs.fetch(series_dict, initial_date='2007-01-01')

df.plot()
plt.show()
