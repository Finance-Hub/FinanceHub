# -*- coding: utf-8 -*-

from selenium import webdriver
from datetime import date
import time
import json
import os

# Load DataBase
with open('cdi.json') as f:
    data = json.load(f)

db_id = len(data['di'])

banner = """
******************** Quantequim - FinLab ********************

                    B3 CDI Data Acquisiton

@author: Sylvio Campos Neto
*****************************************************************

crawling data...

"""
os.system('cls')
print(banner)

# web Crawler
driver = webdriver.Firefox()
driver.get('http://www.b3.com.br/pt_br/')
time.sleep(20)

tax = driver.find_element_by_id('taxaPct')
dt = driver.find_element_by_id('taxaData')

di_data = date.today().strftime('%Y') + '-' + dt.text[3:5] + '-' + dt.text[0:2]
di_taxa = tax.text.replace(',','.')[0:4]

# Crawler output
row_str = """
CDI Data: {}
CDI Taxa: {}
""".format(di_data, di_taxa)
print(row_str)

if data['di'][db_id - 1]['Data'] == di_data:
    print('Data already in database')
else:
    data['di'].append({'id': len(data['di']), 'Data': di_data, 'DI': di_taxa})
    json.dump(data,f)
    print('Data insert success')
