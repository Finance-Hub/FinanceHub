from DataAPI import FRED

fred = FRED()

df = fred.fetch('GDPC1')
