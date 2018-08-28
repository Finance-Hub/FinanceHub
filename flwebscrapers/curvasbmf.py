import requests
import pandas as pd
from bs4 import BeautifulSoup
import execjs

url = 'http://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-sistema-pregao-enUS.asp'

response = requests.get(url, params={'Data': '08/01/2018', 'Mercadoria': 'DI1'})

soup = BeautifulSoup(response.text, 'html.parser')

script = soup.find("script", text=lambda text: text and 'tableShow' in text and "<table" in text).get_text()

# script = """
# var MercadoFut0 = {},
#     MercadoFut1 = {},
#     MercadoFut2 = {};
# var tableShow = function () {};
#
# function getTables() {
#     %s
#     return [MercFut1, MercFut2, MercFut3];
# }
# """ % script
#
# ctx = execjs.compile(script)
# table1, table2, table3 = ctx.call("getTables")
#
# # parse tables into dataframes
# df1 = pd.read_html(table1)[0]
# df2 = pd.read_html(table2)[0]
# df3 = pd.read_html(table3)[0]
#
# print(df1)
# print(df2)
# print(df3)

shit = 1