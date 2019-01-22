"""
@author: Vitor Eller (@VFermat)
"""

from scipy.interpolate import interp1d
from math import log, exp


class FlatForward(object):
    """This class has the abilities of creating a Flat Forward interpolation on a specific set of
    swap rates.

    To understand its use, read the `interpolate` function documentation or the ReadMe page. 
    """


    def interpolate(self, rates, maturities,
                    desired_maturities, convention_days):
        """Function responsible for activating a FlatForward interpolation method
        on a specific set of rates.
        
        Arguments
        ----------
            rates : list
                A List or a Numpy ndarray containing a collection of rates (Real Ones).
            maturities : list
                A List or a Numpy ndarray containing a collection of maturities (On DU unities).
            desired_maturities {list}
                A List or a Numpy ndarray containing the maturities which you want to
                calculate the rates (On DU unities).
            convention_days : int
                Int which representates the convention of the year (252 for Business Days, 365 for Days, etc.).
        
        
        Return
        ----------
            desired_rates : list
                A list containing the rates the user wanted. Indexing correspond desired_maturities indexing.
        """

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
        discount = log(discount)
        return discount

    @staticmethod
    def _convert_discount(discount, maturity, convention_days):

        discount = exp(discount)
        rate = (1/discount)**(convention_days/maturity) - 1
        rate = rate*100
        return rate
