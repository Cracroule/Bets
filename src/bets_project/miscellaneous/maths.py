from math import sqrt, log, exp, pi
import datetime

SOLVER_DEBUG_MODE = False


# approximated
def cumulative_normal_distribution(x):
    (a1, a2, a3, a4, a5) = (0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429)
    l = abs(x)
    k = 1.0 / (1.0 + 0.2316419 * l)
    w = 1.0 - 1.0 / sqrt(2*pi)*exp(-l*l/2.) * (a1*k + a2*k*k + a3*pow(k, 3) + a4 * pow(k, 4) + a5 * pow(k, 5))
    if x < 0:
        w = 1.0 - w
    return w


def poisson_probability(k_events, lambda_param):
    k_fact = 1.
    for i in range(k_events):
        k_fact *= i + 1.
    return lambda_param**k_events * exp(- lambda_param) / k_fact


# approximated (shifted part)
def poisson_proba_table(lambda_param, k_max=10):
    unshifted_prob = [poisson_probability(k, lambda_param) for k in range(k_max + 1)]
    total_prob = sum(unshifted_prob)
    shifted_prob = [prob / total_prob for prob in unshifted_prob]
    return shifted_prob


# dichotomy implementation, might be improved
def solver(f, x_min, x_max, eps):
    if f(x_min) * f(x_max) > 0:
        if SOLVER_DEBUG_MODE:
            print("no roots between ", x_min, " and ", x_max)
        raise Exception("no solution found in solver")
    else:
        c = (x_min + x_max) / 2.
        while x_max - x_min >= eps:
            c = (x_min + x_max) / 2.
            if f(x_min) * f(c) <= 0:
                x_max = c
            else:
                x_min = c
        return c


def time_series_stats(time_series):
    ts_sum = sum(time_series)
    ts_square_sum = sum([t*t for t in time_series])
    avg = ts_sum / len(time_series)
    sigma = ts_square_sum / len(time_series) - avg * avg
    return avg, sigma


# class ResultsWeighting(object):
#
#     def __init__(self):
#         raise NotImplementedError('attempt to instantiate abstract class ResultsWeighting')
#
#     def weight(self, t2, t1):
#         raise NotImplementedError()
#
#
# class ExponentialWeight(ResultsWeighting):
#
#     def __init__(self, discount_rate, day_count_base=365.):
#         self.param = discount_rate
#         self.day_count_base = day_count_base
#
#     def weight(self, t2, t1):
#         time_diff = t2 - t1
#         if time_diff.days < 0:
#             raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
#         return exp(- self.param * time_diff.days / self.day_count_base)
#
#
# class LinearWeight(ResultsWeighting):
#
#     def __init__(self, horizon):
#         self.param = horizon
#
#     def weight(self, t2, t1):
#         time_diff = t2 - t1
#         if time_diff.days < 0:
#             raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
#         return max(1. - time_diff.days / self.param, 0.)
