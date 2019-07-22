
# coding: utf-8

# In[150]:
#Authors: Alisson Arrais; Bachir Chaouiche; Rafael Gartner;Thiago Fernandes

import numpy as np
import scipy.stats
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
get_ipython().run_line_magic('matplotlib', 'inline')

# load data with prices
def load_data():
    df = pd.read_excel('Dados para VaR em python.xlsx')
    return df

def calc_portfolio(df_prices,df_par):
# '''
# :param df: pandas dataframe with stock prices a
# :param df_prices: pandas dataframe with parameters
# '''        
    df_prices = df_prices.sort_index(ascending = True)
    df_ret = pd.DataFrame(index = df_prices.index, columns = df_prices.columns)
    df_pl= pd.DataFrame(index = df_prices.index,columns = df_prices.columns)
    for stock in df_prices:     
        ret_series = df_prices[stock].pct_change()
        profit_loss_serie = ret_series*df_par[stock].DELTA
        df_ret[stock] = pd.DataFrame(ret_series)
        df_pl[stock] = pd.DataFrame(profit_loss_serie)
    return df_ret.dropna(),df_pl.dropna()

def calculate_single_asset_var(returns_Series):
    rets = returns_Series
    rets = rets.dropna(how='any') 
    rets = rets.sort_index(ascending = True)
    var  = np.percentile(rets, 5)
    # RETURN HISTOGRAM
    plt.figure(figsize = (10,6))
    plt.hist(rets,density=True, alpha = 0.6,  histtype='bar', rwidth=0.8, facecolor="b")
    plt.xlabel('Returns')
    plt.ylabel('Frequency')
    plt.title(r'Histogram of {}'.format(rets.name), fontsize=18, fontweight='bold')
    plt.axvline(x=var, color='r', linestyle='--', label='95% Confidence VaR: ' + "{0:.2f}%".format(var * 100))
    plt.legend()
    plt.show()  

    #VaR values
    print ("99.99% VaR: " , "{0:.2f}%".format(np.percentile(rets, .01) * 100))
    print ("99% VaR: " + "{0:.2f}%".format(np.percentile(rets, 1) * 100))
    print ("95% VaR: " + "{0:.2f}%".format(np.percentile(rets, 5) * 100))
    
    
def calculate_multi_asset_var(df_pl):
    df_pl['PORTFOLIO_VALUE'] = df_pl.sum(axis=1)

    port_rets = df_pl['PORTFOLIO_VALUE']
    port_rets = port_rets.sort_values(axis=0, ascending=True)


    var =  np.percentile(port_rets, .01)
    var1 =  np.percentile(port_rets, 1)
    var2 =  np.percentile(port_rets, 5)

    # RETURN HISTOGRAM
    plt.figure(figsize = (10,6))
    plt.hist(port_rets,density=True, alpha = 0.6,  histtype='bar', rwidth=0.8, facecolor="b")
    plt.xlabel('Portfolio Returns')
    plt.ylabel('Frequency')
    plt.title(r'Histogram of Stock Portfolio Returns', fontsize=18, fontweight='bold')
    plt.axvline(x=var2, color='r', linestyle='--', label='Price at Confidence Interval: R$ ' + str(round(var2, 2)))
    plt.legend()
    plt.show() 

    #VaR values
    print ("99.99% VaR: " , "R$ {0:.2f}".format(round(var, 2)))
    print ("99% VaR: " + "R$ {0:.2f}".format(round(var1, 2)))
    print ("95% VaR: " + "R$ {0:.2f}".format(round(var2, 2)))


df_prices = load_data()
df_prices.set_index('Data', inplace = True)
start = df_prices.index.min().date()
end   = df_prices.index.max().date()

# create a portfolio to test
AMOUNT = pd.Series([1000,1000,1000,1000,1000,1000,1000])
AMOUNT.name = 'Investment Amount'

# buy price is the first price we have in dataset
PRICE = df_prices.loc[start]
AMOUNT.index = PRICE.index
POSITION = PRICE * AMOUNT
N = AMOUNT.count()
indices = ['AMOUNT', 'PRICE', 'DELTA']
df_par = pd.DataFrame({'AMOUNT':AMOUNT, 'PRICE': PRICE, 'DELTA':POSITION}).T
df_ret,df_pl =  calc_portfolio(df,df_par)


# In[147]:


calculate_single_asset_var(df_ret.BOVA11)


# In[137]:


calculate_multi_asset_var(df_pl)

