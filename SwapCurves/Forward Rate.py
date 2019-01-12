

#1. As Datas
#2. As Maturities
#3. Rate dos dois Maturities
#4. Quantos dias úteis as maturities tem da data inicial
#Taxa Forward

import numpy as np
import datetime


def forward_rate(base_date, maturity1, maturity2, rate1, rate2, convention):

    maturity1_date = base_date + datetime.timedelta(days=maturity1)
    maturity2_date = base_date + datetime.timedelta(days=maturity2)

    business_days1 = np.busday_count( base_date, maturity1_date )
    business_days2 = np.busday_count( base_date, maturity2_date )

    days_to_years1 = (business_days1/convention)
    days_to_years2 = (business_days2/convention)

    numerator = (1+rate1)**days_to_years2
    denominator = (1+rate2)**days_to_years1

    get_forward = ((numerator/denominator)-1)*100

    return get_forward



base_date = datetime.date(2002, 1, 18)
maturity1 = 14
maturity2 = 40
rate1 = 0.1903
rate2 = 0.1899

print(forward_rate(base_date, maturity1, maturity2, rate1, rate2, 252))


