"""
Author: Vitor Eller
"""

from webscrapers import CETIP
import matplotlib.pyplot as plt

cetip = CETIP()

df = cetip.fetch('MediaCDI', initial_date='2015-08-20', end_date='2015-08-25')

df.plot()
plt.show()
