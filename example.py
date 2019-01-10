# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 17:10:40 2019

@author: Vitor Eller
"""

import pandas as pd

df = pd.read_excel('clean_data.xlsx')

df.loc['3M'].plot()

from Days import SwapCurve

sc = SwapCurve(df, 'business_days')

dates = list(df.columns)[257:260]

terms = [48, 59, 157, 2574]

methods = ['quadratic', 'cubic', 'linear', 'nearest']

info = sc.get_rate(dates, terms, methods)

sc.plot_day_curve(dates, interpolate=False, interpolate_methods=methods, scatter=False)