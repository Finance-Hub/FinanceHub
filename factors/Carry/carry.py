"""
Carry - Time Series and Cross Sectional
2019-07-22
Grupo: 
Alan Sing
Camila Salum
Fernanda Caiafa
Vanessa Lutz
"""


#import packages
import numpy as np
import pandas as pd
import xlrd
import matplotlib.pyplot as plt
from scipy.optimize import minimize  # optimization function
from tqdm import tqdm  # this will just make thing a bit prettier


#users may change that
strDir = "C:\\Users\\pontu\\Downloads\\python_tests\\carrydb\\"
#shrink correlation parameters
cov_window = 63 #cov length, working days
shrinkage_parameter = 0.5 #calculated correlation will be reduced by half with this default
#bounds parameters
minExp = -0.2
maxExp = 0.2
#optimization parameters
targetVol = 0.04
targetBeta = 0
maxTotalExp = 2
#smooth operator
iSmoothOp = 22	#rolling window, wd


# import data
strFile = "G10_rates_carry_data.xlsx"
#spot rates (i guess there´s no need of loading this anymore...)
df_zcc = pd.read_excel(strDir + strFile, sheet_name='spot_rates', header = 3, index_col=1)
df_zcc = df_zcc.iloc[:,1:]

#carry signal
df_carry = pd.read_excel(strDir + strFile, sheet_name='carry_signal', header = 3, index_col=1)
df_carry = df_carry.iloc[:,1:]

#tracker
df_trackers = pd.read_excel(strDir + strFile, sheet_name='swap_trackers', header = 3, index_col=1)
df_trackers = df_trackers.iloc[:3996,1:]

#no carry, no tracker
df_trackers = df_trackers[~pd.isnull(df_carry)]



#shrink correlation
df_returns = df_trackers.pct_change(1)
cov_matrix = df_returns.shift(1).rolling(cov_window).cov()  # notice the 1 day lag - we use yestrday's information to trade today
corr_matrix = df_returns.shift(1).rolling(cov_window).corr()  # notice the 1 day lag - we use yestrday's information to trade today

#we must speak in the same language - same dates carry and trackers - dates
df_carry = df_carry.reindex(df_trackers.index).fillna(method='ffill')
calendar = cov_matrix.dropna(how='all').index.get_level_values(0).unique()

#gen empty matrix
shrunk_cov_matrix = pd.DataFrame(index=corr_matrix.index, columns=corr_matrix.columns)
df_vols = pd.DataFrame(index=calendar, columns=df_trackers.keys())
df_betas = pd.DataFrame(index=calendar, columns=df_trackers.keys())

#loop to calc - tqdm: cool way of doing this
for d in tqdm(calendar, 'Covariances and Betas'):
	
	# find the available countris for date d
	available_countries = list(cov_matrix.loc[d].dropna(how='all').dropna(how='all', axis=1).index)
	
	# gets the diagonal covariance matrix and turn it to standard deviation
	vols = np.diag(np.array(cov_matrix.loc[d][available_countries].loc[available_countries]).diagonal()**0.5)
	
	# shrunk correlation matrix - convex combination between the estimated matrix and the identity matrix
	corr = (1 - shrinkage_parameter) * np.array(corr_matrix.loc[d][available_countries].loc[available_countries]) + shrinkage_parameter * np.eye(len(vols))
	
	# builds the shrunk covariance matrix
	shrunk_cov_matrix.loc[d].loc[available_countries, available_countries] = vols.dot(corr).dot(vols) * 252
	
	# saves the volatilities and (shrunk) betas (cov/var) against USD bond
	df_vols.loc[d][available_countries] = vols.diagonal()
	df_betas.loc[d][available_countries] = shrunk_cov_matrix.loc[d, 'USD'][available_countries] / shrunk_cov_matrix.loc[d, 'USD'].loc['USD']


#low exposoure fund
#TO DO: improve it to became generic
ExpBounds = {'USD': [minExp, maxExp],  # United States
                  'EUR': [minExp, maxExp],  # Eurozone
                  'GBP': [minExp, maxExp],  # UK
                  'CAD': [minExp, maxExp],  # Canada
                  'JPY': [minExp, maxExp],  # Japan
                  'AUD': [minExp, maxExp],  # Australia
                  'NZD': [minExp, maxExp],  # New Zeland
                  'CHF': [minExp, maxExp],  # Switzerland
                  'SEK': [minExp, maxExp],  # Sweden
                  'NOK': [minExp, maxExp]}  # Norway


bounds = pd.DataFrame(data=ExpBounds, index=['lower', 'upper']).T



#set optimization and do it
#creates weight matrix
df_weights = pd.DataFrame(index=calendar, columns=df_trackers.keys())

#loop
for d in tqdm(calendar, 'Weights Optimization'):
	
	#pick what´s available that time
	available_countries = list(cov_matrix.loc[d].dropna(how='all').dropna(how='all', axis=1).index)
	
	#cov, beta and carry values
	cov = np.array(shrunk_cov_matrix.loc[d, available_countries].loc[available_countries])
	betas = np.array(df_betas.loc[d, available_countries])
	mu = np.array(df_carry.loc[d, available_countries])
	
	#equations
	port_carry = lambda w: -mu.dot(w)
	port_net_vol = lambda w: float(w.dot(cov).dot(w.T))**0.5
	port_gross_weights = lambda w: np.sum(np.abs(w))
	port_beta = lambda w: np.dot(betas, w)
	
	#set constraints
	cons = ({'type': 'ineq', 'fun': lambda w: targetVol - port_net_vol(w)},
            {'type': 'eq', 'fun': lambda w: targetBeta - port_beta(w)},
            {'type': 'ineq', 'fun': lambda w: maxTotalExp - port_gross_weights(w)})
	
	#initial values
	w0 = np.zeros(len(available_countries))
	
	#optimize - minimization
	res = minimize(fun=port_carry,
                   x0=w0,
                   method='SLSQP',
                   bounds=bounds.loc[available_countries].values,
                   constraints=cons)
	
	if res.success:
		df_weights.loc[d][available_countries] = res.x

#result        
df_weights = df_weights.fillna(method='ffill')
#smooth operator: rolling window
df_smooth_weights = df_weights.rolling(iSmoothOp).mean()

#Build the Index for the Strategy
calendar = df_smooth_weights.dropna(how='all').index
df_tracker_diff = df_trackers.diff(1)
strat_index = pd.DataFrame(index=calendar, columns=['tr_index'])

#starting in 100 basis
strat_index['tr_index'].iloc[0] = 100
#holdings = quantity
holdings = (strat_index['tr_index'].iloc[0] * df_smooth_weights.loc[calendar[0]])/ df_trackers.iloc[0,:]

#loop to calc
for d, dm1 in tqdm(zip(calendar[1:], calendar[:-1])):
    pnl = (holdings * df_tracker_diff.loc[d]).sum()
    strat_index['tr_index'].loc[d] = strat_index['tr_index'].loc[dm1] + pnl
    holdings = (strat_index['tr_index'].loc[d] * df_smooth_weights.loc[d])/df_trackers.loc[d]


#plot resutls
strat_index['tr_index'].plot(figsize=(15, 8))
plt.show()
