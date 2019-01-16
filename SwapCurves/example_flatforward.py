import pandas as pd
from Days import SwapCurve

data = pd.read_excel('clean_data.xlsx')

date = [data.columns[45]]

sc = SwapCurve(data, 'business_days')

sc.plot_day_curve(date, interpolate=True, interpolate_methods=['flatforward'])