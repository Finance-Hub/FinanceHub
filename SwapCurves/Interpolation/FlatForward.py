"""
@author: Vitor Eller
"""

from scipy.interpolate import interp1d


class FlatForward(object):

    def interpolate(self, rates, maturities,
                    desired_maturities, convention_days):

        discounts = [self._convert_rate(rate, maturity, convention_days) for
                     rate, maturity in zip(rates, maturities)]
        interp_func = interp1d(maturities, discounts)

        desired_rates = []
        for maturity in desired_maturities:
            discount = interp_func(maturity)
            rate = self._convert_discount(discount, maturity, convention_days)
            desired_rates.append(rate)

        return desired_rates

    @staticmethod
    def _convert_rate(rate, maturity, convention_days):

        rate = rate/100
        discount = 1/((1+rate)**(maturity/convention_days))
        return discount

    @staticmethod
    def _convert_discount(discount, maturity, convention_days):

        rate = (1/discount)**(convention_days/maturity) - 1
        rate = rate*100
        return rate
