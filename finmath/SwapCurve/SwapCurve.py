"""
Authors: Vitor Eller (@Vfermat) and Liam Dunphy (@ldunphy98)
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt

from scipy.interpolate import interp1d
from math import log, exp
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime
from finmath.SwapCurve.Holidays.AnbimaHolidays import AnbimaHolidays


class SwapCurve(object):

    interpolate_display = {
            'linear': 'r-',
            'cubic': 'g--',
            'quadratic': 'b:',
            'nearest': 'y-.',
            'flatforward': 'r-'
            }

    conventions = {
            'business_days': 252,
            'calendar_days': 360
            }

    calendars = {
        'br_anbima': AnbimaHolidays().get_holidays()
    }

    def __init__(self, rates, convention='business_days',
                 calendar='br_anbima'):
        """[summary]

        Arguments
        ----------
            rates : pandas df
                Rates should be a pandas dataframe where the columns are the
                maturity of the title and the rows should be `datetime` type.
                For more information, check the `ReadMe.md` document.

        Keyword Arguments
        ----------
            convention : str (default: {'business_days'})
                Your calendar convention. For options, check the `ReadMe.md` document.
            calendar : str (default: {'br_anbima'})
                Which holidays should the code use.
                For now, only Br - Anbima is implemented.
        """

        self.convention = convention
        self.convention_year = self.conventions[convention]
        self.rates = rates
        self.holidays = self.calendars[calendar]

    def plot_3d(self, plot_type='surface'):
        """Function to plot the surface of the swap curve.

        Keyword Arguments
        ----------
            plot_type : str (default: {'surface'})
                Which type of plot you want to see. You can choose either `surface` or `wireframe`
        """

        x = self.rates.index
        y = self.rates.columns
        # Creating 2D Array with swap rates
        z = []
        for column in y:
            base_curve = self.rates[column]
            curve = self._get_3d_curve(base_curve, x)
            z.append(curve)
        z = np.array(z)
        # Converting x (maturities terms) to days to maturities
        x = [self._days_in_term(term, self.convention) for term in x]
        # Converting y (dates) to number. Otherwise, plot will not work
        inty = [0]
        for date in y:
            if date != y[0]:
                diff = date - y[0]
                inty.append(diff.days)
        y = inty
        # Creating 2D arrays for x and y
        x, y = np.meshgrid(x, y)

        # Plotting Graphic
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        if plot_type == 'surface':
            ax.plot_surface(y, x, z)
        elif plot_type == 'wireframe':
            ax.plot_wireframe(y, x, z)
        else:
            raise ValueError('Invalid Plot Type. Please read documentation for valid plots.')
        ax.set_xlabel('Date')
        ax.set_ylabel('Days to Maturity')
        ax.set_zlabel('Swap Rate (%)')
        plt.show()

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
            `nearest` and `flatforward`.

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
                                                 n_desired_terms, method,
                                                 self.convention_year)
                rates = {k: v for k, v in zip(n_desired_terms,
                                              irates)}
                for k in rates.keys():
                    info[method].at[curve.name, k] = rates[k]

        return info

    def get_historic_forward(self, maturity1, maturity2, plot=False,
                             interpolate_method='cubic'):
        """Function that returns the historic of the forward rate between two maturities. 
        Maturities have to be between max and min maturities for that title.

        Arguments
        ----------
            maturity1 : int
                Lower Maturity.
            maturity2 : int
                Higher Maturity

        Keyword Arguments
        ----------
            plot : bool (default: {False})
                Let the user decide if he wants to plot the historic or not.
            interpolate_method {str} (default: {'cubic'})
                Let the user decide which Interpolation Method will be used.
        """

        historic = pd.Series()
        for i in range(len(self.rates.columns)):
            date = self.rates.columns[i]
            rate1 = self.get_rate([date], [maturity1],
                                  [interpolate_method])[interpolate_method][maturity1][date]
            rate2 = self.get_rate([date], [maturity2],
                                  [interpolate_method])[interpolate_method][maturity2][date]
            forward = self._forward_rate(date, maturity1, maturity2,
                                         rate1, rate2, self.convention_year)
            historic.at[date] = forward
        if plot:
            historic.plot()
            plt.show()

        return historic

    def get_historic_rates(self, maturity, plot=False):
        terms = self.rates.index
        day_terms = [self._days_in_term(term, self.convention) for term in terms]
        if maturity in day_terms:
            historic_rates_curve = self.rates.loc[maturity]
            if plot:
                historic_rates_curve.plot()
                plt.show()
            return historic_rates_curve
        else:
            dates = list(self.rates.columns)
            response = self.get_rate(dates, [maturity])
            table_term = response["cubic"][maturity]
            if plot:
                table_term.plot()
                plt.show()
            return table_term

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
            date = date.strftime('%d/%b/%Y')
            if interpolate:
                if len(interpolate_methods) == 1:
                    terms = curve.index
                    dterms = [self._days_in_term(t, self.convention) for
                              t in terms]
                    iterms = np.arange(min(dterms), max(dterms), 1)
                    irates = self._interpolate_rates(dterms, list(curve),
                                                     iterms,
                                                     interpolate_methods[0],
                                                     self.convention_year)
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
                                                         iterms, method,
                                                         self.convention_year)
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

    def get_historic_duration(self, maturity, plot=False):

        durations = pd.Series()
        # term = self._days_in_term(maturity, self.convention)
        term = maturity
        for date in self.rates.columns.values:
            rate = self.get_rate([date], [term])["cubic"][term]
            duration = self._get_duration(maturity, float(rate), self.convention_year)
            durations.at[date] = float(duration)

        if plot:
            durations.plot()
            plt.show()

        return durations

    def _get_3d_curve(self, base_curve, maturities):

        icurve = base_curve.copy()
        icurve = icurve.dropna()

        icurve_maturities = icurve.index
        icurve_dmaturities = [self._days_in_term(term, self.convention) for
                              term in icurve_maturities]
        max_maturity = max(icurve_dmaturities)
        min_maturity = max(icurve_dmaturities)
        date = base_curve.name

        for maturity in maturities:
            dmaturity = self._days_in_term(maturity, self.convention)
            if (dmaturity > min_maturity and dmaturity < max_maturity) and dmaturity not in icurve_dmaturities:
                rate = self.get_rate(date, dmaturity)['cubic'][dmaturity]
                base_curve[maturity] = rate

        return base_curve

    @staticmethod
    def _get_duration(maturity, rate, convention):

        rate = rate/100
        numerator = maturity/convention
        duration = - numerator / (1+rate)

        return duration

    @staticmethod
    def _interpolate_rates(day_terms, rates, interp_terms,
                           method, convention_days):

        if method != 'flat_forward':
            func = interp1d(day_terms, rates, kind=method)
            interp_rates = [func(day) for day in interp_terms]
        else:
            ff = FlatForward()
            interp_rates = ff.interpolate(rates, day_terms,
                                          interp_terms, convention_days)

        return interp_rates

    @staticmethod
    def _days_in_term(term, rules):

        rule = {
                'D': {
                        'business_days': 1,
                        'calendar_days': 1
                        },
                'W': {
                        'business_days': 5,
                        'calendar_days': 7
                        },
                'M': {
                        'business_days': 22,
                        'calendar_days': 30
                        },
                'Y': {
                        'business_days': 252,
                        'calendar_days': 360
                        }
        }

        term_time = term[-1]
        multiplication = int(term[0:-1])

        maturity = rule[term_time][rules]

        term_days = maturity * multiplication

        return term_days

    @staticmethod
    def _forward_rate(base_date, maturity1, maturity2,
                      rate1, rate2, convention):

        rate1 = rate1/100
        rate2 = rate2/100
        holidays = AnbimaHolidays().get_holidays()

        maturity1_date = base_date + dt.timedelta(days=maturity1)
        print(maturity1_date)
        print(base_date)
        maturity2_date = base_date + dt.timedelta(days=maturity2)

        business_days1 = np.busday_count(np.array(base_date).astype('datetime64[D]'),
                                         np.array(maturity1_date).astype('datetime64[D]'), holidays=holidays)
        business_days2 = np.busday_count(np.array(base_date).astype('datetime64[D]'),
                                         np.array(maturity2_date).astype('datetime64[D]'), holidays=holidays)

        days_to_years1 = (business_days1/convention)
        days_to_years2 = (business_days2/convention)

        numerator = (1+rate2)**days_to_years2
        denominator = (1+rate1)**days_to_years1

        get_forward = ((numerator/denominator)-1)*100

        return get_forward


class FlatForward(object):
    """This class has the abilities of creating a Flat Forward interpolation
    on a specific set of swap rates.
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
