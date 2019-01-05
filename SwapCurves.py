"""
@author: Vitor Eller - @VFermat
"""

from scipy.interpolate import interp1d

class SwapCurves(object):
    
    def __init__(self):
        self.active = False
    
    def get_rate_at_day(self, day_count, interpol_method):
        
        """
        Accepted methods: 
            linear, cubic, nearest, previous, next
        """
        
        if not self.active:
            raise ValueError('Class is not activated. Please activate it.')
            
        self.interpol_func = interp1d(self.term_days, self.rates, kind=interpol_method)
        rate = self.interpol_func(day_count)
        
        return rate
    
    def get_discount_at_day(self, day_count, interpol_method, convention):
        
        if not self.active:
            raise ValueError('Class is not activated. Please activate it.')
            
        try:
            rate = self.interpol_func(day_count)
        except:
            rate = self.get_rate_at_day(day_count, interpol_method)
            
        discount = self._zero_to_discount(day_count, rate, convention)
        
        return discount
            
        
    def convert_discounts(self, discounts, term, convention, update_class=False):
        
        rates = []
        term_days = []
        
        for discount, t in zip(discounts, term):
            
            days = self._get_term_days(t, convention)
            rate = self._discount_to_zero(days, discount, convention)
            rates.append(rate)
            term_days.append(days)
        
        if update_class:
            self.rates = rates
            self.term = term
            self.term_days = term_days
            self.active = True
            
        return rates
    
    def convert_zeros(self, zeros, term, convention, update_class=False):
        
        discounts = []
        term_days = []
        
        for zero, t in zip(zeros, term):
            
            days = self._get_term_days(t, convention)
            discount = self._zero_to_discount(days, zero, convention)
            discounts.append(discount)
            term_days.append(days)
            
        if update_class:
            self.discounts = discounts
            self.term = term
            self.term_days = term_days
            self.active = True
            
        return discounts
            
    
    @staticmethod
    def _zero_to_discount(time, rate, convention='year'):
        
        rate = rate/100
        
        convention_dic = {
                'business_days': 252,
                'year': 360
                }
        
        if convention in convention_dic.keys():
            convention_days = convention_dic[convention]
        else:
            print('Invalid Convention. Full Year will be used (360 days)')
            convention_days = convention_dic['year']
            
        discount_factor = round(1/((1+rate)**(time/convention_days)), 6)
        
        return discount_factor
    
    @staticmethod
    def _discount_to_zero(time, discount, convention='year'):
        
        convention_dic = {
                'business_days': 252,
                'year': 360
                }
        
        if convention in convention_dic.keys():
            convention_days = convention_dic[convention]
        else:
            print('Invalid Convention. Full Year will be used (360 days)')
            convention_days = convention_dic['year']
            
        zero_rate = (1/discount)**(convention_days/time) - 1
        zero_rate = round(100*zero_rate, 5)
                    
        return zero_rate
    
    @staticmethod
    def _get_term_days(term, convention):
        
        conventions = {
                'D': {
                        'year': 1,
                        'business_days': 1
                        },
                'W': {
                        'year': 7,
                        'business_days': 5
                        },
                'M': {
                        'year': 30,
                        'business_days': 21
                        },
                'Q': {
                        'year': 90,
                        'business_days': 63
                        },
                'Y': {
                        'year': 360,
                        'business_days': 252
                        }}
        
        term_type = term[-1]
        times = int(term.split(term_type)[0])
        
        d = conventions[term_type][convention]
        
        term_days = times*d
        
        return term_days
        