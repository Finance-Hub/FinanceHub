import pandas as pd
import requests

key_string_center = '</tr><td class="text-center">'
sep_string_center = '<td class="text-center">'
sep_string_right = '<td class="text-right">'
str_sep = '</td>'
merc_identifier = 'MercFut3 = MercFut3 + '
item_sep = ';'

mercadoria = 'DI1'
data = '08/01/2018'

url = 'http://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-sistema-pregao-enUS.asp'

header = ['MATURITY_CODE', 'OPEN_INTEREST_OPEN', 'OPEN_INTEREST_CLOSE', 'NUMBER_OF_TRADES', 'TRADING_VOLUME',
          'FINANCIAL_VOLUME', 'JUNK1', 'PREVIOUS_SETTLEMENT', 'INDEXED_SETTLEMENT', 'OPENING_PRICE', 'MINIMUM_PRICE',
          'MAXIMUM_PRICE', 'AVERAGE_PRICE', 'LAST_PRICE', 'SETTLEMENT_PRICE', 'CHANGE', 'LAST_BID', 'LAST_OFFER']

response = requests.get(url, params={'Data': data, 'Mercadoria': mercadoria})

resp_str = response.text

df = pd.DataFrame(columns=header)

isrunning = True

lkeyc = len(key_string_center)
lsepc = len(sep_string_center)
lsepr = len(sep_string_right)

while isrunning:
    if resp_str.find(key_string_center) > -1:
        sidx = resp_str.find(key_string_center)  # start of core string
        eidx = sidx + lkeyc + resp_str[sidx + lkeyc:].find(merc_identifier)  # end of core string
        core = resp_str[sidx:eidx]
        core_v = core.split(item_sep)
        resp_str = resp_str[eidx:]  # trimming
        row_df = pd.DataFrame(index=data, columns=header)

"""
* parei na parte em que tenho que procurar os valores dentro da lista core_v
"""