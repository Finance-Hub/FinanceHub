import pandas as pd
from webscrapers import BrazilianBonds


bb = BrazilianBonds()

df = bb.scrape(initial_year = "2021", end_year = "2021", initial_month = "2", end_month = "3")

df
