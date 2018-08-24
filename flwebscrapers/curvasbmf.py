import requests
import pandas as pd
from bs4 import BeautifulSoup

url = 'http://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-sistema-pregao-enUS.asp'

response = requests.get(url, params={'Data': '08/01/2018', 'Mercadoria': 'DI1'})

soup = BeautifulSoup(response.content, 'html.parser')
