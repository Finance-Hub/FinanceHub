




def get_duration(self, maturity, rate, convention):

    rate = rate/100

    numerator = maturity/convention

    duration = - numerator / (1+rate)

    return duration



print(get_duration(1, 300, 5, 252))


