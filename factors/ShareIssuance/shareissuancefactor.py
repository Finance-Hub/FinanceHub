"""
Author: Raphael Gondo
This routine is incomplete and still needs some adjustments
"""

import pandas as pd
import numpy as np
import os
from pandas.tseries.offsets import *

# Note that ccm, comp and crsp_m are WRDS datasets. However, the code is useful for
# # other datasets as long they are panel datasets in conformity to those from WRDS.
# # There are some methodology idiosyncrasies of the US dataset, acc. Fama-French (1993),
# # but once understood, the adaptation to other country dataset is totally feasible.

###################
# CRSP Block      #
###################

## permco is a unique permanent identifier assigned by CRSP to all companies with issues on a CRSP file
## permno identifies a firm's security through all its history, and companies may have several stocks at one time
## shrcd is a two-digit code describing the type of shares traded. The first digit describes the type of security traded.
## exchcd is a code indicating the exchange on which a security is listed

## change variable format to int
crsp_m[['permco','permno','shrcd','exchcd']]=crsp_m[['permco','permno',
      'shrcd','exchcd']].astype(int)

## Line up date to be end of month day, no adjustment on time, but on pattern
crsp_m['date']=pd.to_datetime(crsp_m['date'])
crsp_m['jdate']=crsp_m['date']+MonthEnd(0)

crsp_m = crsp_m[(crsp_m['date'].dt.year > 1993)] # This increases velocity of the algorithm,
# but pay attention on this, as it limits the dataset.

## adjusting for delisting return
dlret.permno=dlret.permno.astype(int)
dlret['dlstdt']=pd.to_datetime(dlret['dlstdt'])
dlret['jdate']=dlret['dlstdt']+MonthEnd(0) ## pick the delist date and put into the EoP

## merge the crsp dataset with the dlret on the left indexes
crsp = pd.merge(crsp_m, dlret, how='left',on=['permno','jdate'])
crsp['dlret']=crsp['dlret'].fillna(0)
crsp['ret']=crsp['ret'].fillna(0)
crsp['retadj']=(1+crsp['ret'])*(1+crsp['dlret'])-1 ## adjusting for delisting return
crsp['me']=crsp['prc'].abs()*crsp['shrout'] # calculate market equity
crsp=crsp.drop(['dlret','dlstdt','prc','shrout'], axis=1)
## axis = 0 is the row, and is default, and axis = 1 is the column to drop
crsp=crsp.sort_values(by=['jdate','permco','me'])
## sorting columns ascending = TRUE as default, by the variables: jdate is the adj date by the EoP and
## permco is the CRSP number for stocks, and me is the market equity.

### Aggregate Market Cap ###
## sum of me across different permno belonging to same permco a given date
crsp_summe = crsp.groupby(['jdate','permco'])['me'].sum().reset_index()
## reset the index to the prior numbers as default in pandas,
## and with the changed index still there drop = False as default

# largest mktcap within a permco/date
crsp_maxme = crsp.groupby(['jdate','permco'])['me'].max().reset_index()
# join by jdate/maxme to find the permno
crsp1=pd.merge(crsp, crsp_maxme, how='inner', on=['jdate','permco','me'])
## join : {‘inner’, ‘outer’}, default ‘outer’. Outer for union and inner for intersection.

## drop me column and replace with the sum me
crsp1=crsp1.drop(['me'], axis=1)
## join with sum of me to get the correct market cap info
crsp2=pd.merge(crsp1, crsp_summe, how='inner', on=['jdate','permco'])
## sort by permno and date and also drop duplicates
crsp2=crsp2.sort_values(by=['permno','jdate']).drop_duplicates()

## keep December market cap
crsp2['year']=crsp2['jdate'].dt.year
crsp2['month']=crsp2['jdate'].dt.month
decme=crsp2[crsp2['month']==12]
decme=decme[['permno','date','jdate','me','year']].rename(columns={'me':'dec_me'})

### July to June dates
crsp2['ffdate']=crsp2['jdate']+MonthEnd(-6) ## MonthEnd(-6) is to go six months in the EoM backwards
crsp2['ffyear']=crsp2['ffdate'].dt.year
crsp2['ffmonth']=crsp2['ffdate'].dt.month
crsp2['1+retx']=1+crsp2['retx'] ## retx is the holding period return w/o dividends for a month
crsp2=crsp2.sort_values(by=['permno','date'])

# cumret by stock ## pick the before year
crsp2['cumretx']=crsp2.groupby(['permno','ffyear'])['1+retx'].cumprod() ## compute the cumulative return
## of a year measured by ffyear, the data date backwards six months.

# lag cumret
crsp2['lcumretx']=crsp2.groupby(['permno'])['cumretx'].shift(1)
## shift one row (as default, axis = 0), this leads to the next period.

# lag market cap by one month
crsp2['lme']=crsp2.groupby(['permno'])['me'].shift(1)

## if first permno then use me/(1+retx) to replace the missing value
crsp2['count']=crsp2.groupby(['permno']).cumcount()
crsp2['lme']=np.where(crsp2['count']==0, crsp2['me']/crsp2['1+retx'], crsp2['lme'])
## insert a 'nan' if the count is zero, or pick the lag one market cap.

# baseline me ## pick the first month of this backwards year, and say it is the base.
mebase=crsp2[crsp2['ffmonth']==1][['permno','ffyear', 'lme']].rename(columns={'lme':'mebase'})

## merge result back together
crsp3=pd.merge(crsp2, mebase, how='left', on=['permno','ffyear'])
crsp3['wt']=np.where(crsp3['ffmonth']==1, crsp3['lme'], crsp3['mebase']*crsp3['lcumretx'])
## and really use the returns to take out the dividends distributed (but what about them?)
## wt is the adjusted lag me without dividends basically, by constructing a cum ret measure.
## the weight should have a criterium, and lagged me seems to be it. Not the current
## me, but six months behind one.


#######################
# CCM Block           #
#######################

## Compustat and CRSP merged data

ccm['linkdt']=pd.to_datetime(ccm['linkdt']) ## linkdt  is a calendar date marking the first effective
## date of the current link. If the link was valid before CRSP's earliest record, LINKDT is set to be
## SAS missing code ".B".
ccm['linkenddt']=pd.to_datetime(ccm['linkenddt']) ## LINKENDDT is the last effective date of the link record.
## It uses the SAS missing code ".E" if a link is still valid.
# if linkenddt is missing then set to today date
ccm['linkenddt']=ccm['linkenddt'].fillna(pd.to_datetime('today'))


###########################
### Net issuance Block  ###
###########################

# The previous part is default for the CRSP dataset, but the following is
# the adaptive part to construct other type of portfolios.

# load share issuance original data
# =============================================================================
# os.chdir('C:\\Users\\n3o_A\\Google Drive (raphael.gondo@usp.br)\\Doutorado Insper\\Finlab\\Finhub project ')
# share_issuance = pd.read_stata('Share_issuance.dta')
# share_issuance = share_issuance[share_issuance['exchcd'] != 0]
# share_issuance = share_issuance[['permno','date','vol','shrout','cfacshr']]
# share_issuance.to_stata('Share_issuance2.dta')
# =============================================================================

# load share issuance simplified data
os.chdir('C:\\Users\\n3o_A\\Google Drive (raphael.gondo@usp.br)\\Doutorado Insper\\Finlab\\Finhub project')
share_issuance = pd.read_stata('Share_issuance2.dta')

# adjust for nan and zero values
share_issuance = share_issuance[pd.notnull(share_issuance['cfacshr'])]
share_issuance = share_issuance[share_issuance['cfacshr'] != 0]

# generate the adjustment factor for shares outstanding
df = share_issuance.set_index(['permno','date'])
firsts = (df.groupby(level=['permno']).transform('first'))
result = df['cfacshr'] / firsts['cfacshr']
result = result.reset_index()
result=result.rename(columns={'cfacshr':'adj_cfac'})

# adjust the shares outstanding by the adjustment factor above
share_issuance = pd.merge(share_issuance, result, how='inner', on=['permno','date'])
share_issuance['adj_out_shs'] = share_issuance['shrout']*share_issuance['adj_cfac']
share_issuance['adj_out_shs'].tail() # just a test to see if the last ones have values.

share_issuance = share_issuance.sort_values(by=['permno','date']).drop_duplicates()
share_issuance['jdate']=share_issuance['date']+MonthEnd(0)

# number months observations
share_issuance['count']=share_issuance.groupby(['permno']).cumcount()

# make the cumulative share issuance for -17 to -6 months
share_issuance['adj_out_shs'] = share_issuance['adj_out_shs'].astype(float)
share_issuance['ln_adj_out_shs'] = np.log(share_issuance['adj_out_shs'])

share_issuance['ln_shs_6'] = share_issuance.groupby(['permno'])['ln_adj_out_shs'].shift(6)
share_issuance['ln_shs_17'] = share_issuance.groupby(['permno'])['ln_adj_out_shs'].shift(17)

share_issuance['shs_iss'] = share_issuance['ln_shs_6'] - share_issuance['ln_shs_17']

###########################
#### Portfolios Block  ####
###########################

# make the usual portfolio schemes to make the asset pricing factor
ccm1=pd.merge(share_issuance[['permno','jdate','shs_iss', 'count']],ccm,how='left',on=['permno'])

# set link date bounds
ccm2=ccm1[(ccm1['jdate']>=ccm1['linkdt'])&(ccm1['jdate']<=ccm1['linkenddt'])]
ccm2=ccm2[['gvkey','permno','jdate','shs_iss', 'count']]

# create a market cap variable
crsp_m['me']=crsp_m['prc'].abs()*crsp_m['shrout'] # calculate market equity

# link comp and crsp
ccm5=pd.merge(crsp_m, ccm2, how='inner', on=['permno', 'jdate'])

## select NYSE stocks for bucket breakdown
## exchcd = 1 (NYSE) and positive beme and positive me and at least 2 years in comp and shrcd in (10,11), resp.
nyse=ccm5[(ccm5['exchcd']==1) & (ccm5['count']>1) & ((ccm5['shrcd']==10) | (ccm5['shrcd']==11))]

nyse = pd.merge(ccm5[['gvkey', 'jdate', 'shs_iss']], nyse, how='inner', on=['gvkey', 'jdate', 'shs_iss'])

# size breakdown ## in only two
nyse_sz=nyse.groupby(['jdate'])['me'].median().to_frame().reset_index().\
                    rename(columns={'me':'sizemedn'})

# momentum breakdown ## in three
nyse_netshs=nyse.groupby(['jdate'])['shs_iss'].describe(percentiles=[0.3, 0.7]).reset_index()
nyse_netshs=nyse_netshs[['jdate','30%','70%']].rename(columns={'30%':'netshs30', '70%':'netshs70'})

nyse_breaks = pd.merge(nyse_sz, nyse_netshs, how='inner', on=['jdate'])

# join back size and momentum breakdown
ccm5 = pd.merge(ccm5, nyse_breaks, how='left', on=['jdate'])

# function to assign sz and share issuance buckets
def sz_bucket(row):
    if row['me']==np.nan:
        value=''
    elif row['me']<=row['sizemedn']:
        value='S'
    else:
        value='B'
    return value

def netshs_bucket(row):
    if   row['shs_iss']<=row['netshs30']:
        value = 'L'
    elif row['shs_iss']<=row['netshs70']:
        value='M'
    elif row['shs_iss']>row['netshs70']:
        value='H'
    else:
        value=''
    return value

# assign size portfolio
ccm5['szport']=np.where((ccm5['me']>0)&(ccm5['count']>=1),
        ccm5.apply(sz_bucket, axis=1), '')
# assign share issuance portfolio
ccm5['netshsport']=np.where((ccm5['me']>0)&(ccm5['count']>=1),
        ccm5.apply(netshs_bucket, axis=1), '')
# create nonmissport variable
ccm5['nonmissport']=np.where((ccm5['netshsport']!=''), 1, 0)

# store portfolio assignment monthly
monthly=ccm5[['permno', 'jdate', 'netshsport','szport','nonmissport']]
monthly['ffyear']=monthly['jdate'].dt.year

# merge back with monthly records
crsp3 = crsp3[['permno','shrcd','exchcd','retadj','me','wt','cumretx','ffyear','jdate']]
ccm3=pd.merge(crsp3,
        monthly[['permno','ffyear','szport','netshsport','nonmissport']],
        how='left', on=['permno','ffyear'])

# keeping only records that meet the criteria
ccm4=ccm3[(ccm3['wt']>0)& (ccm3['nonmissport']==1) &
          ((ccm3['shrcd']==10) | (ccm3['shrcd']==11))]

# function to calculate value weighted return
def wavg(group, avg_name, weight_name):
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return np.nan

# value-weigthed return
vwret=ccm4.groupby(['jdate','szport','netshsport']).apply(wavg, 'retadj',
                  'wt').to_frame().reset_index().rename(columns={0: 'vwret'})
vwret['sbport']=vwret['szport']+vwret['netshsport']
## return to 'sbport' the portfolios that the stocks enter 'szport' and 'bmport' are strings,
## so they compose 'sbport': 'SL', 'SM'..., 'BM', 'BH'.

# firm count
vwret_n=ccm4.groupby(['jdate','szport','netshsport'])['retadj'].count().reset_index().\
                    rename(columns={'retadj':'n_firms'})
vwret_n['sbport']=vwret_n['szport']+vwret_n['netshsport']

# tranpose
ap_factors=vwret.pivot(index='jdate', columns='sbport', values='vwret').reset_index()
ap_nfirms=vwret_n.pivot(index='jdate', columns='sbport', values='n_firms').reset_index()

# create netshs factors
ap_factors['WL']=(ap_factors['BL']+ap_factors['SL'])/2
ap_factors['WH']=(ap_factors['BH']+ap_factors['SH'])/2
ap_factors['WNSH'] = ap_factors['WL']-ap_factors['WH']

ap_factors=ap_factors.rename(columns={'jdate':'date'})

# n firm count
ap_nfirms['L']=ap_nfirms['SL']+ap_nfirms['BL']
ap_nfirms['H']=ap_nfirms['SH']+ap_nfirms['BH']
ap_nfirms['NSH']=ap_nfirms['H']+ap_nfirms['L']

ap_nfirms=ap_nfirms.rename(columns={'jdate':'date'})

os.chdir('C:\\Users\\n3o_A\\Google Drive (raphael.gondo@usp.br)\\Doutorado Insper\\\Finlab\\Finhub project ')
writer = pd.ExcelWriter('ap_factors_net_iss.xlsx')
ap_factors.to_excel(writer,'WNSH')
writer.save()

ap_factors['WNSH'].mean()

