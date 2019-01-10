"""
Authors: Vitor Eller (@Vfermat) and Liam Dunphy (@ldunphy98)
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.interpolate import interp1d


class SwapCurve(object):

    interpolate_display = {
            'linear': 'r-',
            'cubic': 'g--',
            'quadratic': 'b:',
            'nearest': 'y-.'
            }

    def __init__(self, rates, convention):
        """
        convention options:
            business_days
            calendar_days
        rates options:
            pandas dataframe
        """
        self.convention = convention
        self.rates = rates

    def get_rate(self, base_curves, desired_terms,
                 interpolate_methods=['cubic']):
        """
        Function that get the Swap Rate for a specific term. It calculates
        based on the interpolation of the base curve.

        Parameters
        ----------
        base_curves : array_like
            Curves that will be used on the interpolation, to discover the
            rate for a specific term.
        desired_terms : array_like
            Terms you want to find the swap rate. Should be passed as days.
            (future development will allow you to input a desired date.)
        interpolate_methods : array_like, optional
            Methods used to interpolate the curve. Only works if `interpolate`
            is True. Default is 'cubic'.

            Accepted methods are: `linear`, `cubic`, `quadratic`,
            and `nearest`.

        Returns
        ----------
        info : dict
            A dictionary containing the rates for the asked terms. If more than
            one base curve is used, there will be one rate for each term, for
            each base curve.

            The dictionary has two `levels`, being as follow:
                info = {'interpolate_method': {'term': 'rate'}}
        """

        # Checking inputs
        if type(base_curves) not in (list, np.ndarray):
            raise TypeError("Argument 'base_curves' should be array_like.")
        if type(desired_terms) not in (list, np.ndarray):
            raise TypeError("Argument 'desired_terms' should be array_like.")
        if type(interpolate_methods) not in (list, np.ndarray):
            raise TypeError("Argument 'interpolate_methods' should be array_like.")

        # Checking if base_curves are valid:
        curves = []
        for date in base_curves:
            try:
                curve = self.rates[date]
                curve = curve.dropna()
            except IndexError as e:
                print('{}. {} is an invalid date, since there is not a curve for this date. It will not be used.'.format(e, date))
            else:
                curves.append(curve)

        # Checking if there are curves to be plotted
        if len(curves) == 0:
            raise ValueError('There are no Base Curves to be used.')

        # Creating dataFrame with information asked
        info = {}
        for method in interpolate_methods:
            info[method] = pd.DataFrame()
        for curve in curves:
            for method in interpolate_methods:
                terms = curve.index
                dterms = [self._days_in_term(t, self.convention) for
                          t in terms]
                n_desired_terms = desired_terms.copy()
                # Checks if desired_terms are valid
                for term in desired_terms:
                    if term < min(dterms) or term > max(dterms):
                        print('{} is an invalid term.'.format(term))
                        n_desired_terms.remove(term)
                irates = self._interpolate_rates(dterms, list(curve),
                                                 n_desired_terms, method)
                rates = {k: v for k, v in zip(n_desired_terms,
                                              irates)}
                for k in rates.keys():
                    info[method].at[curve.name, k] = rates[k]

        return info

    def plot_day_curve(self, dates, interpolate=False,
                       interpolate_methods=['cubic'], scatter=False):
        """
        Function to plot the SwapCurve for a specific set of days.

        Parameters
        ----------
        dates : array_like
            Dates to be plotted.

            Obs: A great improvement would be to allow the user to pick a date
            that we do not have the curve, and plot it. So basically construct
            the curve for a specific day, based on near ones.
        interpolate : boolean, optional
            If you want to create and interpolation of the curve or not.
            If interpolate is False, curve plotted will be similar to a
            `linear` interpolation. Default is False.
        interpolate_methods : array_like, optional
            Methods used to interpolate the curve. Only works if `interpolate`
            is True. Default is 'cubic'.

            Accepted methods are: `linear`, `cubic`, `quadratic`,
            and `nearest`.
        scatter : boolean, optional
            Only works if `interpolate` is False. If `scatter` is True, then
            instead of plotting something close to a `linear` interpolation,
            the graphic will look like a scatter plot.

        See Also
        ----------
        plot_term_historic : plot the historic rate for the desired term
        """
        """
        TO DO:
            - implement algorithm that lets the user pick any date,
            even if we don't have that specific curve
            - Change de xlabel to the term, instead of
            letting it show 'days to maturity'
        """
        # Checking Inputs
        if type(dates) not in (list, np.ndarray):
            raise TypeError("Argument 'dates' should be array_like.")
        if type(interpolate_methods) not in (list, np.ndarray) and interpolate_methods is not None:
            raise TypeError("If you desire to interpolate, argument 'interpolate_method' should be a list")

        # Gathering curves information.
        curves = []
        for date in dates:
            try:
                curve = self.rates[date]
                curve = curve.dropna()
            except IndexError as e:
                print('{}. {} is an invalid date. It will not be used.'.format(e, date))
            else:
                curves.append(curve)
           
        # Check if there are curves to be plotted (or all dates where invalid)
        if len(curves) == 0:
            raise ValueError('There are no dates to be plotted.')

        plotted = False
        # Start plotting
        for curve in curves:
            date = curve.name
            date = date.split()[0]
            date = date.split('-')
            date = date[::-1]
            date = '/'.join(date)
            if interpolate:
                if len(interpolate_methods) == 1:
                    terms = curve.index
                    dterms = [self._days_in_term(t, self.convention) for
                              t in terms]
                    iterms = np.arange(min(dterms), max(dterms), 10)
                    irates = self._interpolate_rates(dterms, list(curve),
                                                     iterms,
                                                     interpolate_methods[0])
                    plt.plot(iterms, irates, label=date)
                    plt.legend()
                    plt.xlabel('Days to Maturity')
                    plt.ylabel('Swap Rate (%)')
                else:
                    """
                    If there are more than one interpolation method to be used
                    ther will be created an specific graphic for each desired
                    date (if there are more than one). This happens to
                    ensure visualization of the data.
                    """
                    terms = curve.index
                    dterms = [self._days_in_term(t, self.convention) for
                              t in terms]
                    iterms = np.arange(min(dterms), max(dterms), 10)
                    for method in interpolate_methods:
                        plot_type = self.interpolate_display[method]
                        irates = self._interpolate_rates(dterms, list(curve),
                                                         iterms, method)
                        plt.plot(iterms, irates, plot_type, label=method)
                    plt.xlabel('Days to Maturity')
                    plt.ylabel('Swap Rate (%)')
                    plt.title(date)
                    plt.legend()
                    plt.show()
                    plotted = True
            else:
                if not scatter:
                    curve.plot(label=date)
                else:
                    terms = curve.index
                    dterms = [self._days_in_term(t, self.convention) for
                              t in terms]
                    rates = curve.tolist()
                    plt.plot(dterms, rates, 'o', label=date)

        if not plotted:
            plt.xlabel('Days to Maturity')
            plt.ylabel('Swap Rate (%)')
            plt.legend()
            plt.show()

    @staticmethod
    def _interpolate_rates(day_terms, rates, interp_terms, method):

        func = interp1d(day_terms, rates, kind=method)
        interp_rates = [func(day) for day in interp_terms]

        return interp_rates

    @staticmethod
    def _days_in_term(term, rules):

        rule = {
                'D':
                    {'business_days': 1, 'calendar_days': 1},
                'W':
                    {'business_days': 5, 'calendar_days': 7},
                'M':
                    {'business_days': 22, 'calendar_days': 30},
                'Y':
                    {'business_days': 252, 'calendar_days': 360}
            }

        term_time = term[-1]
        multiplication = int(term[0:-1])

        maturity = rule[term_time][rules]

        term_days = maturity * multiplication

        return term_days


"""
TO DO:
    - write documentation
    - 3D Plotting
    - comment code
    - structure bbg api code (pull needed data)
"""
