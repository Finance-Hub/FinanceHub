# -*- coding: utf-8 -*-
"""
Created on Mon Jan  7 10:51:49 2019

@author: Vitor Eller
"""

rates = [0.12200, 0.12604, 0.14625, 0.15607, 0.17850, 
         0.22850, 0.27700, 0.28940, 0.30418]

terms = ['1D', '2D', '1W', '2W', '1M', '2M', 
         '3M', '4M', '5M']

from SwapCurves import SwapCurves
import matplotlib.pyplot as plt

sc = SwapCurves()

discounts = sc.convert_zeros(rates, terms, 'year', True)
dates = [i for i in range(1, 150)]
rate = [sc.get_rate_at_day(i, 'cubic') for i in dates]

plt.plot(dates, rate)
