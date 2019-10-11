"""
@author: Daniel Dantas de Castro
"""

#import
from B3_webscrapper_v2 import ScraperB3Curves

#instantiate a class instance
SB3C = ScraperB3Curves()

#call sample 1
vAns1 = SB3C.scrape("PRE", "2019-08-19", "2019-08-21")
vAns1

#call sample 2
vAns2 = SB3C.scrape("DIC", "2019-08-19", "2019-08-21")
vAns2

#call sample 3
vAns3 = SB3C.scrape("DOC", "2019-08-19", "2019-08-21")
vAns3

#call sample 4
vAns4 = SB3C.scrape("INP", "2019-08-19", "2019-08-21")
vAns4

#call sample 5
vAns5 = SB3C.scrape("TODOS", "2019-08-18", "2019-08-18")
vAns5

#call sample 6
vAns6 = SB3C.scrape("TODOS", "2019-08-16", "2019-08-16")
vAns6
