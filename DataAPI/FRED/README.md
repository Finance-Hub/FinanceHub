# FRED
The `FRED` class allows you to grab time series data from the Federal
Reserve Economic Data (FRED) database of St. Louis FED.

## Getting Started
The FRED class allows you to grab time series data from the database of
the Federal Reserve Economic Data (FRED) database of St. Louis FED.
This is essentially a wrapper around their txt url. The main contents
of the database are macroeconomic time series for the US. To find a
series, you need to search for its ID code on
[this website](https://fred.stlouisfed.org/). This class only has the
`fetch` method, which receives the ID of a series (or a list of IDs)
and returns a pandas DataFrame with the series.

### Simple Example
The series ID for the Seasonally Adjusted Real GDP of the US is GDPC1.

``` python
from DataAPI import FRED
fred = FRED()
df = fred.fetch('GDPC1')
```

# Author
Gustavo Curi Amarante
