import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

country_code = {'US': '082',  # United States
                'AU': '127',  # Australia
                'CA': '101',  # Canada
                'GE': '910',  # Germany
                'UK': '110',  # United Kingdom
                'JP': '105'}  # Japan

tenors_month = [3, 6, 12, 2*12, 3*12, 4*12, 5*12, 6*12, 7*12, 8*12, 9*12, 10*12, 15*12, 20*12, 30*12]


def gen_ticker(tenor, country):
    """
    This function generates the ticker for a given country and tenor.
    """

    if tenor < 12:
        t_code = '0' + str(tenor) + 'M Index'

    else:
        t_code = str(int(tenor/12)).zfill(2) + 'Y Index'

    ticker = 'F' + country_code[country] + t_code

    return ticker


def calc_duration(ytm, t=10, dy=0.0001):

    ytm_minus = ytm - dy
    ytm_plus = ytm + dy
    price0 = 100/((1+ytm) ** t)
    price_minus = 100/((1+ytm_minus) ** t)
    price_plus = 100 / ((1 + ytm_plus) ** t)
    dur = (price_minus - price_plus)/(2*price0*dy)

    return dur


# ===== READ THE ZERO COUPON CURVES =====
df_zcc = pd.read_excel(r'data\zero coupon curves.xlsx',
                       sheet_name='values',
                       index_col='Dates').multiply(1/100)

# ===== READ THE TRACKERS =====
df_trackers = pd.DataFrame()
for ctry in country_code.keys():
    df = pd.read_excel(r'data\df_' + str(ctry) + '.xlsx')
    tracker = df['er_index']
    tracker.name = ctry
    df_trackers = pd.concat([df_trackers, tracker], axis=1)

df_trackers.plot()
plt.show()

# ===== BUILD CARRY SIGNAL ====
df_carry = pd.DataFrame()

for ctry in country_code.keys():

    print('Building Carry for', ctry)

    ticker_list = [gen_ticker(t, ctry) for t in tenors_month]  # gets the tickers for thar country
    df_ctry = df_zcc[ticker_list]  # gets the verticies for the country

    df_curve = pd.DataFrame(index=df_ctry.index, columns=list(range(3, 30 * 12 + 1)), dtype=float)

    for t, tick in zip(tenors_month, ticker_list):
        if t in tenors_month:
            df_curve[t] = df_ctry[tick]

    df_curve = df_curve.dropna(how='all').interpolate(axis=1, method='pchip')

    dur = calc_duration(ytm=df_curve[12 * 10])
    ctry_carry = df_curve[10*12] - df_curve[3] - dur*(df_curve[10*12] - df_curve[9*12 + 9])
    ctry_carry.name = ctry
    df_carry = pd.concat([df_carry, ctry_carry], axis=1)

df_carry.plot()
plt.show()

# ===== BUILD WEIGHTS =====
N = df_carry.shape[1]
avg_rank = ((1 + N)*N)/(2*N)
c = (df_carry.rank(axis=1).iloc[-1] - avg_rank).abs().sum()/2
df_weights = (df_carry.rank(axis=1) - avg_rank)/c

df_weights.plot()
plt.show()

# ===== BUILD STRATEGY INDEX =====
df_returns = df_trackers.pct_change(1)
df_returns[['US', 'JP']].plot()
plt.show()

strat_index = pd.DataFrame(data={'Return': (df_weights * df_returns).dropna().sum(axis=1),
                                 'Level': np.nan})

strat_index['Level'].iloc[0] = 100

for d, dm1 in zip(strat_index.index[1:], strat_index.index[:-1]):
    strat_index['Level'].loc[d] = strat_index['Level'].loc[dm1] * (1 + strat_index['Return'].loc[d])

strat_index['Level'].plot()
plt.show()
