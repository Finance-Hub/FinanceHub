"""
Authors: Vitor Eller (@Vfermat) and Liam Dunphy (@ldunphy98)
"""

import matplotlib.pyplot as plt

class SwapCurve(object):
    
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
        
    def plot_day_curve(self, date):
        """
        TO DO:
            - implement algorithm that lets the user pick any date, even if we don't have
            that specific curve
            - Create interpolation function
        """
        
        try:
            curve = self.rates[date]
        except:
            raise ValueError('Date not available, try again.')
        else:
            """
            Codigo para a interpolacao
            terms = curve.columns
            maturities = [self._days_in_term(t, self.convention) for t in terms]
    
            """
            curve.plot(legend=date)
            plt.label(True)
            plt.show()

    def plot_historic_rates(self, maturity)
         try:
            curve1= self.rates[maturity]
         except:
            raise ValueError('Maturity not available, try again.')
         else:

            curve1.plot(legend=date)
            plt.label(True)
            plt.show()






 @staticmethod
    def _days_in_term(term, rules):
    
        rule= {'D':
                    {'business_days':1, 'calendar_days':1},
                 'W':
                    {'business_days':5, 'calendar_days':7},
                 'M':
                    {'business_days':22, 'calendar_days':30},
                 'Y':
                     {'business_days': 252, 'calendar_days': 360}
    
                 }
    
        term_time = term[-1]
        multiplication = term[0:-1]
    
        days_until_maturity = rule[term_time][rules]
    
        term_days = days_until_maturity * multiplication
    
        return term_days





