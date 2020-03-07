import pandas as pd
from tqdm import tqdm
from calendars import DayCounts

dc = DayCounts('BUS/252', calendar='anbima')

# BW path
# file_path = r'C:\Users\gamarante\Dropbox\Aulas\Insper - Financas Quantitativas\VNA Raw.xlsx'

# macbook path
# file_path = r'/Users/gusamarante/Dropbox/Aulas/Insper - Financas Quantitativas/VNA Raw.xlsx'

# mac path
file_path = r'/Users/gustavoamarante/Dropbox/Aulas/Insper - Financas Quantitativas/VNA Raw.xlsx'

df_mensal = pd.read_excel(file_path, 'Mensal', index_col=0)
df_diario = pd.read_excel(file_path, 'Diario', index_col=0, na_values=['#N/A N/A'])
df_release = pd.read_excel(file_path, 'Release')
df_release.columns = ['Date', 'IPCA']

df = pd.DataFrame(index=pd.date_range('2003-03-18', 'today', freq='D'),
                  columns=['dia util', 'ultima virada', 'DU desde virada', 'DU entre viradas', 'time fraction',
                           'proj anbima', 'saiu IPCA', 'ultimo IPCA', 'proj IPCA', 'ultimo index', 'VNA'])
df.index.name = 'Date'

df['dia util'] = dc.isbus(df.index)

# TODO com certeza existe um meio mais eficiente de fazer isso
for d in tqdm(df.index, 'Filling "ultima virada"'):
    if d.day >= 15:
        df.loc[d, 'ultima virada'] = pd.datetime(d.year, d.month, 15)
    else:
        if d.month - 1 == 0:
            df.loc[d, 'ultima virada'] = pd.datetime(d.year-1, 12, 15)
        else:
            df.loc[d, 'ultima virada'] = pd.datetime(d.year, d.month-1, 15)

df['DU desde virada'] = dc.days(df['ultima virada'], df.index)
df['DU entre viradas'] = dc.days(df['ultima virada'], df['ultima virada'] + pd.DateOffset(months=1))
df['time fraction'] = df['DU desde virada'] / df['DU entre viradas']

df['proj anbima'] = df_diario['Anbima+0']/100
df['proj anbima'] = df['proj anbima'].fillna(method='ffill')

df.loc[df.index[0], 'saiu IPCA'] = df_release.index.isin([df.index[0]]).any()

for d, dm1 in tqdm(zip(df.index[1:], df.index[:-1]), 'Filling "saiu IPCA"'):
    if d.day <= 15 and df.loc[dm1, 'saiu IPCA']:
        df.loc[d, 'saiu IPCA'] = True
    else:
        df.loc[d, 'saiu IPCA'] = df_release['Date'].isin([d]).any()

# fill 'ultimo IPCA' column
df_aux = df.index.to_frame()
df_aux.index.name = None
df_aux = pd.merge_asof(df_aux, df_release)
df_aux = df_aux.set_index('Date')
df['ultimo IPCA'] = df_aux['IPCA']/100

df['proj IPCA'] = df['saiu IPCA']*df['ultimo IPCA'] + (1 - df['saiu IPCA'])*df['proj anbima']

# Ultimo Index do IPCA
df_aux = df['ultima virada'].to_frame('Dates')
df_aux['Dates'] = pd.to_datetime(df_aux['Dates'])
df_aux = pd.merge_asof(df_aux, df_mensal.reset_index()[['Dates', 'IPCA Index']])
df_aux.index = df.index
df['ultimo index'] = df_aux['IPCA Index']

# VNA
df['VNA'] = 1000*(df['ultimo index']/1614.62)*((1+df['proj IPCA'])**df['time fraction'])

# drop non business days
df = df[df['dia util']]
df_vna = df['VNA']

# ==== Price ====
df = pd.concat([df['VNA'], df_diario['Yield B50']], axis=1).dropna(how='all')
df['Yield B50'] = df['Yield B50'].fillna(method='ffill')
df = df.dropna(how='any')
df['Cupom'] = 0

dcf_dates = pd.date_range(start='2012-08-15', end='2050-08-15', freq='12SMS')
dcf_dates = dc.busdateroll(dcf_dates, 'following')
df_dcf = pd.DataFrame(index=dcf_dates)

for d in tqdm(df.index, 'Pricing'):

    vna_d = df.loc[d, 'VNA']
    rate_d = df.loc[d, 'Yield B50']/100

    df_dcf['DU'] = dc.days(d, df_dcf.index)

    df_dcf['Fluxo'] = ((1.06**0.5) - 1) * vna_d
    df_dcf.loc['2050-08-15', 'Fluxo'] = df_dcf.loc['2012-08-15', 'Fluxo'] + vna_d

    df_dcf['Fluxo Descontado'] = df_dcf['Fluxo']/((1+rate_d)**(df_dcf['DU']/252))
    df.loc[d, 'PU'] = df_dcf['Fluxo Descontado'].sum()

    if d in dcf_dates:
        df.loc[d, 'Cupom'] = ((1.06**0.5) - 1) * vna_d

df['Quantidade'] = 1 + (df['Cupom'].shift(1, fill_value=0)/df['PU']).expanding().sum()
df['Notional'] = df['Quantidade'] * df['PU']

df.to_clipboard()
