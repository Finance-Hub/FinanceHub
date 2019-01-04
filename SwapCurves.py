"""
@author: Vitor Eller - @VFermat
"""

class SwapCurves(object):
    
    def convert_discounts(self, discounts, term, convention):
        
        rates = []
        
        for discount, t in zip(discounts, term):
            
            days = self._get_term_days(t, convention)
            rate = self._discount_to_zero(days, discount, convention)
            rates.append(rate)
            
        return rates
    
    def convert_zeros(self, zeros, term, convention):
        
        discounts = []
        
        for zero, t in zip(zeros, term):
            
            days = self._get_term_days(t, convention)
            discount = self._zero_to_discount(days, zero, convention)
            discounts.append(discount)
            
        return discounts
            
    
    @staticmethod
    def _zero_to_discount(time, rate, convention='year'):
        
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
            
        zero_rate = round((1/discount)**(convention_days/time) - 1, 5)
            
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
        