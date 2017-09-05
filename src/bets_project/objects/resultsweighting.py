from math import exp


class ResultsWeighting(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class ResultsWeighting')

    def weight(self, t2, t1):
        raise NotImplementedError()


class ExponentialWeight(ResultsWeighting):

    def __init__(self, discount_rate, day_count_base=365., allow_negative=False):
        self.param = discount_rate
        self.day_count_base = day_count_base
        self.allow_negative = allow_negative

    def weight(self, t2, t1):
        time_diff = t2 - t1
        if time_diff.days < 0:
            if self.allow_negative:
                return 0.
            raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
        return exp(- self.param * time_diff.days / self.day_count_base)


class LinearWeight(ResultsWeighting):

    def __init__(self, horizon, allow_negative=False):
        self.param = horizon
        self.allow_negative = allow_negative

    def weight(self, t2, t1):
        time_diff = t2 - t1
        if time_diff.days < 0:
            if self.allow_negative:
                return 0.
            raise Exception("'weight' should be called with a positive time difference (match results in the past!)")
        return max(1. - time_diff.days / self.param, 0.)
