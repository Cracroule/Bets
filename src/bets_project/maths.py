from math import sqrt, log, exp, pi
import datetime


#approximated
def cumulative_normal_distribution(X):
    (a1, a2, a3, a4, a5) = (0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429)
    L = abs(X)
    K = 1.0 / (1.0 + 0.2316419 * L)
    w = 1.0 - 1.0 / sqrt(2*pi)*exp(-L*L/2.) * (a1*K + a2*K*K + a3*pow(K,3) +
    a4 * pow(K,4) + a5 * pow(K,5))
    if X<0:
        w = 1.0-w
    return w


def solver(f, min, max, eps):
    if f(min)*f(max)>0 :
        print("pas de racine entre ", min," et ", max)
        raise Exception("no solution found in solver")
    else:
        while max-min>=eps :
            C =(min+max)/2.
            if f(min)*f(C)<=0 :
                max=C
            else :
                min=C
        return C


class ExponentialWeight(object):

    def __init__(self, discount_rate, day_count_base=None):
        self.param = discount_rate
        if day_count_base:
            self.day_count_base = day_count_base
        else:
            self.day_count_base = 365.

    def weight(self, t2, t1):
        time_diff = t2.t1
        if time_diff.days < 0:
            raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
        return exp(- self.param * time_diff.days / self.day_count_base)
