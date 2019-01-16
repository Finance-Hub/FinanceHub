import pandas as pd
from Days import SwapCurve

data = pd.read_excel('clean_data.xlsx')

br_curve = SwapCurve(data, 'business_days')

date = [data.columns[45]]

print(br_curve.get_rate(date, [35])['cubic'][35])