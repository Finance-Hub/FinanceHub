import pandas as pd
from Days import SwapCurve

data = pd.read_excel('clean_data.xlsx')

br_curve = SwapCurve(data, 'business_days')

date = data.columns[45]

maturity1 = 360
maturity2 = 720

br_rate1 = br_curve.get_rate([date], [maturity1])['cubic'][maturity1]
br_rate2 = br_curve.get_rate([date], [maturity2])['cubic'][maturity2]

br_forward = br_curve._forward_rate(date, maturity1, maturity2, br_rate1, br_rate2, 252)
forward_historic = br_curve.get_forward_historic(maturity1, maturity2, plot=True)

print(br_forward)

