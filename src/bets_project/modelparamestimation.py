from bets_project.objects import Match
from math import log
import copy


def get_relative_results_history(match, iterable_results, nb_max_results=None, max_days=None):
    home_team_results, away_team_results = list(), list()
    match_result = None
    for result in iterable_results:

        if result.match == match:
            match_result = result
            continue

        if result.match == match or result.match.date > match.date:
            continue

        if max_days:
            time_to_result = match.date - result.match.date
            if time_to_result.days > max_days:
                continue

        if result.match.home_team == match.home_team or result.match.away_team == match.home_team:
            home_team_results.append(result)
        if result.match.home_team == match.away_team or result.match.away_team == match.away_team:
            away_team_results.append(result)

    home_team_results.sort(key=lambda r: r.match.date)
    away_team_results.sort(key=lambda r: r.match.date)

    if nb_max_results and len(home_team_results) > nb_max_results:
        home_team_results = home_team_results[len(home_team_results) - nb_max_results:]
    if nb_max_results and len(away_team_results) > nb_max_results:
        away_team_results = away_team_results[len(away_team_results) - nb_max_results:]

    return home_team_results, away_team_results, match_result


class ModelParamEstimation(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class ModelParamEstimation')

    def get_parameters(self, **kwargs):
        raise NotImplementedError()

    def get_match_parameters(self, match, results_list):
        raise NotImplementedError()


class PoissonLikelihoodParamEstimation(ModelParamEstimation):

    def __init__(self, nb_observed_matches, default_scored_goals, default_conceded_goals, results_weighting,
                 nb_days_validity_parameters=4, max_days=None, convergence_ratio=0.6, max_likelihood_iterations=1000,
                 epsilon=0.000001):
        self.nb_observed_matches = nb_observed_matches
        self.default_scored_goals = default_scored_goals
        self.default_conceded_goals = default_conceded_goals
        self.results_weighting = results_weighting
        self.nb_days_validity_parameters = nb_days_validity_parameters
        self.max_days = max_days
        self.convergence_ratio = convergence_ratio
        self.max_likelihood_iterations = max_likelihood_iterations
        self.epsilon = epsilon
        self.cache = list()

    # get all params of all teams involved in results
    # (compute them if necessary)
    def get_parameters(self, date, results_list):
        for param_date, teams_params, home_adv_param in self.cache:
            if param_date <= date:
                diff_date = date - param_date
                if diff_date.days < self.nb_days_validity_parameters:
                    return teams_params, home_adv_param
        teams_params, home_adv_param = self._compute_params(date, results_list)
        self.cache.append((date, teams_params, home_adv_param))
        return teams_params, home_adv_param

    # care, for matches m1, m2 on the same weekend, make sure to call this method for m1 first if m1.date < m2.date
    # if so, they can share parameters computations and values
    # else, parameters for m2 will include m1 results, and parameters for m1 will have to be computed again
    def get_match_parameters(self, match, results_list):
        teams_params, home_adv_param = self.get_parameters(match.date, results_list)

        try:
            alpha_home, beta_home = teams_params[match.home_team]['alpha'], teams_params[match.home_team]['beta']
        except KeyError:
            alpha_home, beta_home = self.default_scored_goals, self.default_conceded_goals

        try:
            alpha_away, beta_away = teams_params[match.away_team]['alpha'], teams_params[match.away_team]['beta']
        except KeyError:
            alpha_away, beta_away = self.default_scored_goals, self.default_conceded_goals

        lambda_param = alpha_home * beta_away * home_adv_param['gamma']
        mu_param = alpha_away * beta_home

        return lambda_param, mu_param

    def _compute_params(self, date, results_list):
        results_by_team, all_observed_results = self._prepare_results(date, results_list)
        teams_params, home_adv_param = self._init_params(date, results_by_team, all_observed_results)

        llikelihood = self._pseudo_log_likelihood(date, all_observed_results, teams_params, home_adv_param)
        prec_llikelihood = llikelihood * 2.

        i = 0
        while i < self.max_likelihood_iterations and abs(llikelihood/prec_llikelihood - 1.) > self.epsilon:
            teams_params, home_adv_param = self._param_local_optimum(date, results_by_team, all_observed_results,
                                                                    teams_params, home_adv_param)
            prec_llikelihood = llikelihood
            llikelihood = self._pseudo_log_likelihood(date, all_observed_results, teams_params, home_adv_param)

            i += 1

        have_params_converged = abs(llikelihood/prec_llikelihood - 1.) < self.epsilon

        return teams_params, home_adv_param

    def _pseudo_log_likelihood(self, date, results_list, teams_params, home_adv_param):
        llikelihood = 0
        for r in results_list:
            weight = self.results_weighting.weight(date, r.match.date)
            lambda_param = teams_params[r.match.home_team]['alpha'] * teams_params[r.match.away_team]['beta'] * \
                           home_adv_param['gamma']
            mu_param = teams_params[r.match.away_team]['alpha'] * teams_params[r.match.home_team]['beta']
            llikelihood += weight * (-lambda_param + r.home_goals * log(lambda_param) -
                                    mu_param + r.away_goals * log(mu_param))
        return llikelihood

    def _init_params(self, date, results_by_team, all_results):
        teams_params = dict()
        home_adv_param = dict()

        #init gamma computations
        home_adv_param["gamma"] = 1
        home_adv_param["total_weighted_home_scored"] = 0
        for r in all_results:
            weight = self.results_weighting.weight(date, r.match.date)
            home_adv_param["total_weighted_home_scored"] += weight * r.home_goals

        # init param values to alpha=1 and beta =1
        for team in results_by_team.keys():
            teams_params[team] = {'alpha': 1., 'beta': 1., 'total_weighted_scored': 0., 'total_weighted_conceded': 0.,
                                  'nb_obs': 0, 'sum_weight': 0.}

        # compute weighted scored and conceded goals
        for team, team_results in results_by_team.items():
            for r in team_results:
                weight = self.results_weighting.weight(date, r.match.date)
                scored = r.home_goals if r.match.home_team == team else r.away_goals
                conceded = r.home_goals if r.match.away_team == team else r.away_goals
                teams_params[team]['total_weighted_scored'] += weight * scored
                teams_params[team]['total_weighted_conceded'] += weight * conceded
                teams_params[team]['nb_obs'] += 1.
                teams_params[team]['sum_weight'] += weight

        max_sum_weight = max([teams_params[t]['sum_weight'] for t in results_by_team.keys()])
        for team in results_by_team.keys():
            if teams_params[team]['nb_obs'] < self.nb_observed_matches:
                teams_params[team]['lack_weights'] = max(max_sum_weight - teams_params[team]['sum_weight'], 0.)
                teams_params[team]['lack_scored'] = teams_params[team]['lack_weights'] * self.default_scored_goals
                teams_params[team]['lack_conceded'] = teams_params[team]['lack_weights'] * self.default_conceded_goals
            else:
                teams_params[team]['lack_weights'] = 0.
                teams_params[team]['lack_scored'] = 0.
                teams_params[team]['lack_conceded'] = 0.

        return teams_params, home_adv_param

    def _prepare_results(self, date, iterable_results):
        results_by_team = dict()
        for result in iterable_results:

            if result.match.date >= date:
                continue

            if self.max_days:
                time_to_result = date - result.match.date
                if time_to_result.days > self.max_days:
                    continue

            for team in (result.match.home_team, result.match.away_team):
                if team not in results_by_team.keys():
                    results_by_team[team] = list()
                results_by_team[team].append(result)

        for key in results_by_team.keys():
            results_by_team[key].sort(key=lambda x: x.match.date)
            if self.nb_observed_matches and len(results_by_team[key]) > self.nb_observed_matches:
                results_by_team[key] = results_by_team[key][len(results_by_team[key]) - self.nb_observed_matches:]

        if max([len(x) for x in results_by_team.values()]) < self.nb_observed_matches:
            raise Exception("all teams do not have enough results to observe to assess parameters")

        all_observed_results = set()
        for team_results in results_by_team.values():
            for r in team_results:
                all_observed_results.add(r)

        return results_by_team, sorted(list(all_observed_results), key=lambda x: x.match.date)

    def _param_local_optimum(self, date, results_by_team, all_results, teams_params, home_adv_param):
        new_teams_params = copy.deepcopy(teams_params)
        new_home_adv_param = copy.deepcopy(home_adv_param)

        new_home_adv_param['gamma_tmp'] = 0.
        for team in results_by_team.keys():
            new_teams_params[team]['alpha_tmp'] = 0.
            new_teams_params[team]['beta_tmp'] = 0.

        for team, results in results_by_team.items():
            for r in results:
                weight = self.results_weighting.weight(date, r.match.date)
                other_team = r.match.away_team if team == r.match.home_team else r.match.home_team
                gamma_atk = home_adv_param['gamma'] if r.match.home_team == team else 1.
                gamma_def = 1. if r.match.home_team == team else home_adv_param['gamma']
                new_teams_params[team]['alpha_tmp'] += weight * teams_params[other_team]['alpha'] * gamma_atk
                new_teams_params[team]['beta_tmp'] += weight * teams_params[other_team]['beta'] * gamma_def

        for r in all_results:
            weight = self.results_weighting.weight(date, r.match.date)
            new_home_adv_param["gamma_tmp"] += weight * teams_params[r.match.home_team]['alpha'] * \
                                           teams_params[r.match.away_team]['alpha']
        new_home_adv_param["gamma"] = home_adv_param["total_weighted_home_scored"] / new_home_adv_param["gamma_tmp"]

        # adjustments with missing matches
        for team in results_by_team.keys():
            sum_scored = teams_params[team]['total_weighted_scored'] + teams_params[team]['lack_scored']
            sum_def = new_teams_params[team]['beta_tmp'] + teams_params[team]['lack_weights']

            sum_conceded = teams_params[team]['total_weighted_conceded'] + teams_params[team]['lack_conceded']
            sum_atk = new_teams_params[team]['alpha_tmp'] + teams_params[team]['lack_weights']

            new_teams_params[team]["alpha"] = sum_scored / sum_def
            new_teams_params[team]["beta"] = sum_conceded / sum_atk

        # normalisation
        nb_teams = len(teams_params)
        norm_alpha = nb_teams / sum([new_teams_params[t]["alpha"] for t in new_teams_params.keys()])
        norm_beta = nb_teams / sum([new_teams_params[t]["beta"] for t in new_teams_params.keys()])

        # final values
        for team in new_teams_params.keys():
            new_teams_params[team]["alpha"] = self.convergence_ratio * new_teams_params[team]["alpha"] * norm_alpha +\
                                              (1 - self.convergence_ratio) * teams_params[team]["alpha"]
            new_teams_params[team]["beta"] = self.convergence_ratio * new_teams_params[team]["beta"] * norm_beta +\
                                             (1 - self.convergence_ratio) * teams_params[team]["beta"]

        return new_teams_params, new_home_adv_param


class DiffGoalHomeMadeEstimation(ModelParamEstimation):

    def __init__(self, diff_goal_std_uncertainty, home_goal_diff_advantage, min_expected_results, no_history_penalty,
                 diff_goal_aggregation_multiplier, results_weighting, nb_max_results=None, max_days=None):
        self.sigma = diff_goal_std_uncertainty
        self.home_goal_diff_advantage = home_goal_diff_advantage
        self.min_expected_results = min_expected_results
        self.no_history_penalty = no_history_penalty
        self.results_weighting = results_weighting
        self.diff_goal_aggregation_multiplier = diff_goal_aggregation_multiplier
        self.nb_max_results = nb_max_results
        self.max_days = max_days

    def get_parameters(self, date, results_list):
        raise NotImplementedError('not implemented, please use get_match_parameters')

    def get_match_parameters(self, match, iterable_results):
        home_team_results, away_team_results, match_result = get_relative_results_history(match, iterable_results,
                                                                                          self.nb_max_results,
                                                                                          self.max_days)
        teams = match.home_team, match.away_team
        all_past_results = home_team_results, away_team_results
        estimated_diffs = [0., 0.]
        nb_observed_matches = [0, 0]
        for i in range(2):
            team = teams[i]
            team_results = all_past_results[i]
            weighted_diff_sum = 0.
            weights_sum = 0.
            for r in team_results:
                if r.match.home_team == team:
                    goal_diff = r.home_goals - r.away_goals
                elif r.match.away_team == team:
                    goal_diff = r.away_goals - r.home_goals
                else:
                    raise Exception("'analyse_match': history of results should involve teams of the match")

                weight = self.results_weighting.weight(match.date, r.match.date)
                weighted_diff_sum += weight * goal_diff
                weights_sum += weight
                if weight:
                    nb_observed_matches[i] += 1
            if weights_sum:
                estimated_diff = weighted_diff_sum / weights_sum
            else:
                estimated_diff = 0.
            corrected_estimated_diff = estimated_diff
            if nb_observed_matches[i] < self.min_expected_results:
                corrected_estimated_diff *= nb_observed_matches[i] / self.min_expected_results
                corrected_estimated_diff += self.no_history_penalty * (
                    self.min_expected_results - nb_observed_matches[i]) / self.min_expected_results
            estimated_diffs[i] = corrected_estimated_diff

        match_estimated_diff = self.diff_goal_aggregation_multiplier * (
                estimated_diffs[0] - estimated_diffs[1]) + self.home_goal_diff_advantage

        return match_estimated_diff, self.sigma

