# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 10:54:22 2019

@author: Vitor Eller
"""

import pandas as pd

data = pd.read_excel('Swaps US Dollar.xlsx')

data.columns

info = {}

for c in range(data.columns.size):
    if c % 2 == 0:
        
        date = data.iloc[:, c]
        taxes = data.iloc[:, c + 1]
        tenor = data.columns[c + 1]
        
        info[tenor] = {}
        
        for d, t in zip(date, taxes):
            d = str(d)
            
            info[tenor][d] = t
        
clean_data = pd.DataFrame()        

for k in info.keys():
    df = pd.DataFrame(info[k], index=[k])
    df = df.transpose()
    
    clean_data = pd.concat([clean_data, df], axis=1)

clean_data = clean_data.transpose()    
clean_data.to_excel('us_data.xlsx')