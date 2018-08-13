# FinanceLab - DataAPI

Library for Macroeconomy time series data acquisitions.

### FRED

The `FRED` class allows you to grab time series data from the Federal
Reserve Economic Data (FRED) database of St. Louis FED.

#### Getting Started

The FRED class allows you to grab time series data from the database of
the Federal Reserve Economic Data (FRED) database of St. Louis FED.
This is essentially a wrapper around their txt url. The main contents
of the database are macroeconomic time series for the US. To find a
series, you need to search for its ID code on
[this website](https://fred.stlouisfed.org/). This class only has the
`fetch` method, which receives the ID of a series (or a list of IDs)
and returns a pandas DataFrame with the series.

#### Simple Example

The series ID for the Seasonally Adjusted Real GDP of the US is GDPC1.

``` python
from DataAPI import FRED

fred = FRED()
df = fred.fetch('GDPC1')
```

### IMF

The IMF class allows you to grab macroeconomic and financial data from
the IMF Database. This is essentially a wrapper around their data API.

#### Example

To fetch data with this class you need to know the IMF dataset that has your
series and the values of the query parameters.
The class is built in a way that helps you find the desired series and fill
out the query parameters.
The workflow below gives an example.

### SGS

The `SGS` class allows you to grab time series data from the database of
the brazilian central bank (BCB).

#### Getting Started

The SGS class allows you to grab time series data from the database of
the brazilian central bank (BCB). In portuguese, the database is called
Sistema de Gerenciamento de Series(SGS). This is essentially a wrapper
around their JSON API. The main contents of the database are
macroeconomic time series for brazil. To find a series you need to
search for its ID code on
[this website](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries).
This class only has the `fetch` method, which receives the ID of a
series (or a list of IDs) and returns a pandas DataFrame with the
series.

#### Simple Example

The series ID for the Seasonally Adjusted Real GDP Index of Brazil
is 22109.

``` python
from DataAPI import SGS

sgs = SGS()
df_GDP = sgs.fetch(22109)
```

#### Optional arguments

The arguments of the `fetch` method are:

- `series_ID` (required): string, int or list with the IDs of the desired series
- `initial_date` (optional): date as string in the format `'dd/mm/yyyy'`
- `end_date` (optional): date as string in the format `'dd/mm/yyyy'`

If the date parameters are empty, the method grabs all the available
dates of the series.
