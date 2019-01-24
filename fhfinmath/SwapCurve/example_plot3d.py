"""
@author: Vitor Eller
"""

import pandas as pd
from Days import SwapCurve

data = pd.read_excel('clean_data.xlsx')

sc = SwapCurve(data, 'business_days')

sc.plot_3d()


