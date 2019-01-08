# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 17:10:40 2019

@author: Vitor Eller
"""

import pandas as pd

df = pd.read_excel('clean_data.xlsx')

df.iloc[4]

import matplotlib.pyplot as plt
from Days import SwapCurve

sc = SwapCurve(df, 'business_days')

sc.plot_day_curve(df.columns[197])