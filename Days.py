def days_in_term(term, rules):

    rule= {'D':
                {'business days':1, 'calendar days':1},
             'W':
                {'business days':5, 'calendar days':7},
             'M':
                {'business days':22, 'calendar days':30},
             'Y':
                 {'business days': 252, 'calendar days': 360}

             }

    term_time = term[-1]
    multiplication = term[0:-1]

    maturity = rule[term_time][rules]

    term_days = maturity * multiplication

    return term_days





