from math import sqrt, log, exp, pi
import datetime


#approximated
def cumulative_normal_distribution(x):
    (a1, a2, a3, a4, a5) = (0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429)
    l = abs(x)
    k = 1.0 / (1.0 + 0.2316419 * l)
    w = 1.0 - 1.0 / sqrt(2*pi)*exp(-l*l/2.) * (a1*k + a2*k*k + a3*pow(k, 3) + a4 * pow(k, 4) + a5 * pow(k, 5))
    if x < 0:
        w = 1.0 - w
    return w


def solver(f, x_min, x_max, eps):
    if f(x_min) * f(x_max) > 0:
        print("pas de racine entre ", x_min, " et ", x_max)
        raise Exception("no solution found in solver")
    else:
        while x_max - x_min >= eps:
            C = (x_min + x_max) / 2.
            if f(x_min)*f(C) <= 0:
                x_max = C
            else:
                x_min = C
        return C


class ExponentialWeight(object):

    def __init__(self, discount_rate, day_count_base=None):
        self.param = discount_rate
        if day_count_base:
            self.day_count_base = day_count_base
        else:
            self.day_count_base = 365.

    def weight(self, t2, t1):
        time_diff = t2 - t1
        if time_diff.days < 0:
            raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
        return exp(- self.param * time_diff.days / self.day_count_base)


class LinearWeight(object):

    def __init__(self, horizon, day_count_base=None):
        self.param = horizon
        if day_count_base:
            self.day_count_base = day_count_base
        else:
            self.day_count_base = 365.

    def weight(self, t2, t1):
        time_diff = t2 - t1
        if time_diff.days < 0:
            raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
        return max(1. - time_diff.days / self.param, 0.)
