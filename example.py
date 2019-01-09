# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 17:10:40 2019

@author: Vitor Eller
"""

import pandas as pd

df = pd.read_excel('clean_data.xlsx')

df.iloc[4]


from Days import SwapCurve

sc = SwapCurve(df, 'business_days')

dates = list(df.columns)[175:179]
methods = ['nearest']

sc.plot_day_curve(dates, interpolate=True, interpolate_methods=methods)