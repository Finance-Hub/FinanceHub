import pandas as pd
from Days import SwapCurve

data = pd.read_excel('clean_data.xlsx')

sc = SwapCurve(data, 'business_days')

date = [data.columns[260]]

sc.plot_day_curve(date, interpolate=True, interpolate_methods=['flatforward'])
