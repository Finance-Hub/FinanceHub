# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 17:40:57 2018

@author: Vitor Eller
"""

from getcetipdata import CETIP
import matplotlib.pyplot as plt

cetip = CETIP()

df = cetip.fetch('MediaCDI', initial_date='2015-08-20', end_date='2015-12-25')

df.plot()
plt.show()