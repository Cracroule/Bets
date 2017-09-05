from bets_project.miscellaneous.maths import cumulative_normal_distribution, solver, poisson_proba_table


class ModelMatchOutcomes(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class MatchOutcomeModel')

    def outcomes_probabilities(self, **kwargs):
        raise NotImplementedError()

#
# """ look in past of each team in order to asset probability of issues W/D/A
# This example of implementation assesses a typical goal difference for each team
# And assumes that the expected goal difference of input match follow a normal distribution"""
#

class DiffGoalNormalDistrib(ModelMatchOutcomes):

    def __init__(self):
        pass

    @staticmethod
    def proba_home_win(expected_goal_diff, sigma):
        return 1. - cumulative_normal_distribution((0.5 - expected_goal_diff) / sigma)

    @staticmethod
    def proba_away_win(expected_goal_diff, sigma):
        return cumulative_normal_distribution((-0.5 - expected_goal_diff) / sigma)

    @staticmethod
    def proba_draw(expected_goal_diff, sigma):
        return cumulative_normal_distribution((0.5 - expected_goal_diff) / sigma) - cumulative_normal_distribution(
            (-0.5 - expected_goal_diff) / sigma)

    @staticmethod
    def outcomes_probabilities(expected_goal_diff, sigma):
        p_home_d = DiffGoalNormalDistrib.proba_away_win(expected_goal_diff, sigma)
        p_home_v = DiffGoalNormalDistrib.proba_home_win(expected_goal_diff, sigma)
        p_draw = 1. - p_home_d - p_home_v
        return p_home_v, p_draw, p_home_d

    @staticmethod
    def implied_param_from_proba(proba_list, precision=0.000001, diff_goals_min=-10., diff_goals_max=10.,
                                 min_sigma=0.01, max_sigma=5):
        p1, p2, p3 = proba_list

        def g(s):
            e_diff_s = solver(lambda x: DiffGoalNormalDistrib.proba_home_win(x, s) - p1, diff_goals_min,
                            diff_goals_max, precision)
            return DiffGoalNormalDistrib.proba_draw(e_diff_s, s) - p2

        final_sigma = solver(g, min_sigma, max_sigma, precision)
        final_e_diff = solver(lambda x: DiffGoalNormalDistrib.proba_home_win(x, final_sigma) - p1, diff_goals_min,
                              diff_goals_max, precision)

        return final_e_diff, final_sigma


class GoalsPoissonDistrib(ModelMatchOutcomes):

    default_min_lambda = 0.05
    default_max_lambda = 8.
    default_precision = 0.01

    def __init__(self):
        pass
        # self.default_min_lambda = 0.05
        # self.default_max_lambda = 8.

    @staticmethod
    def distrib_from_poisson_param(lambda_param_1, lambda_param_2, k_max=20):
        table_1 = poisson_proba_table(lambda_param_1, k_max)
        table_2 = poisson_proba_table(lambda_param_2, k_max)

        p_home_v, p_draw, p_home_d = 0., 0., 0.
        for k in range(k_max + 1):
            p_draw += table_1[k] * table_2[k]
            for l in range(0, k):
                p_home_v += table_1[k] * table_2[l]
            for l in range(k + 1, k_max + 1):
                p_home_d += table_1[k] * table_2[l]

        return p_home_v, p_draw, p_home_d

    @staticmethod
    def optimal_poisson_param_given_range(target_probabilities, lambda_1_min, lambda_1_max, precision,
                                          absolute_min_lambda, absolute_max_lambda):

        p1, p2, p3 = target_probabilities

        def g(lambda_param_1):
            f = lambda x: GoalsPoissonDistrib.distrib_from_poisson_param(lambda_param_1, x)[0] - p1
            lambda_param_2 = solver(f, absolute_min_lambda, absolute_max_lambda, precision)
            return GoalsPoissonDistrib.distrib_from_poisson_param(lambda_param_1, lambda_param_2)[1] - p2

        # print " \lambda_1_min", lambda_1_min, "     lambda_1_max", lambda_1_max
        lambda_param_1 = solver(g, lambda_1_min, lambda_1_max, precision)
        lambda_param_2 = solver(lambda x: GoalsPoissonDistrib.distrib_from_poisson_param(lambda_param_1, x)[0] - p1,
                                absolute_min_lambda, absolute_max_lambda, precision)
        return lambda_param_1, lambda_param_2

    # TODO raise specific exception
    @staticmethod
    def implied_param_from_proba(target_probabilities, nb_max_iterations=20, precision=0.000001,
                                              absolute_min_lambda=0.05, absolute_max_lambda=8.):
        lambda_total_possible_range = absolute_max_lambda - absolute_min_lambda
        lambda_sub_range = lambda_total_possible_range / nb_max_iterations
        for i in range(nb_max_iterations):
            try:
                params = GoalsPoissonDistrib.optimal_poisson_param_given_range(target_probabilities, absolute_min_lambda + i * lambda_sub_range,
                                                                               absolute_min_lambda + (i + 1) * lambda_sub_range, precision,
                                                                               absolute_min_lambda, absolute_max_lambda)
                return params
            except:
                continue
        raise Exception("no solution found !")

