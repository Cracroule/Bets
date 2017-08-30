class InvestmentStrategy(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class MatchOutcomeAnalyse')

    def get_investment_amounts(self, **kwargs):
        raise NotImplementedError()


class DummyAwayInvestStrategy(InvestmentStrategy):

    def __init__(self):
        pass

    def get_investment_amounts(self, outcomes_probabilities, booky_quotes):
        return [0., 0., 1.]


class DummyDrawInvestStrategy(InvestmentStrategy):

    def __init__(self):
        pass

    def get_investment_amounts(self, outcomes_probabilities, booky_quotes):
        return [0., 1., 0.]


class DummyHomeInvestStrategy(InvestmentStrategy):

    def __init__(self):
        pass

    def get_investment_amounts(self, outcomes_probabilities, booky_quotes):
        return [1., 0., 0.]


class GenericGainInvestStrategy(InvestmentStrategy):

    def __init__(self, percent_gain_threshold, fct_of_expected_gain):
        self.percent_gain_threshold = percent_gain_threshold
        self.fct_of_expected_gain = fct_of_expected_gain

    def get_investment_amounts(self, outcomes_probabilities, booky_quotes, reversed_strategy=False):
        expected_gains = [outcomes_probabilities[i] * booky_quotes[i] - 1. for i in range(3)]
        max_gain = max(expected_gains)
        if reversed_strategy:
            max_gain = min(expected_gains)
        bet_issue = expected_gains.index(max_gain)

        bet_amount = self.fct_of_expected_gain(abs(max_gain) * 100.) if \
            abs(max_gain) > self.percent_gain_threshold else 0.

        all_bet_amounts = [0., 0., 0.]
        all_bet_amounts[bet_issue] = bet_amount

        return all_bet_amounts