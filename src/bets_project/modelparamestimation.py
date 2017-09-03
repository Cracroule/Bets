from bets_project.objects import Match

class ModelParamEstimation(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class ModelParamEstimation')

    def assess_param(self, **kwargs):
        raise NotImplementedError()


class PoissonLikelihoodParamEstimation(object):

    def __init__(self, nb_observed_matches, default_scored_goals, default_conceded_goals, max_days=None):
        self.nb_observed_matches = nb_observed_matches
        self.default_scored_goals = default_scored_goals
        self.default_conceded_goals = default_conceded_goals
        self.max_days = max_days

    def prepare_results(self, date, iterable_results):
        results_by_team = dict()
        for result in iterable_results:

            if result.match.date > date:
                continue

            if self.max_days:
                time_to_result = date - result.match.date
                if time_to_result.days > self.max_days:
                    continue

            for team in (result.match.home_team, result.match.away_team):
                if team not in results_by_team.keys():
                    results_by_team[team] = list()
            results_by_team[team].append(result)

        for key, val in results_by_team.items():
            val.sort(key=lambda x: x.match.date)
            if self.nb_observed_matches and len(val) > self.nb_observed_matches:
                results_by_team[key] = val[len(val) - self.nb_observed_matches:]

        if max([len(x) for x in results_by_team.values()]) < self.nb_observed_matches:
            raise Exception("all teams do not have enough results to observe to assess parameters")

        all_observed_results = set()
        for team_results in results_by_team.values():
            for r in team_results:
                all_observed_results.add(r)

        return results_by_team, sorted(list(all_observed_results), key=lambda x: x.match.date)

    def pseudo_log_likelihood(self, **kwargs):
        # TODO
        pass

    def assess_param(self, date, results_list, results_weighting, convergence_ratio=0.5):
        results_by_team, all_observed_results = self.prepare_results(date, results_list)
        teams_params, home_adv_param = self.init_params(date, results_by_team, all_observed_results, results_weighting)

    def init_params(self, date, results_by_team, all_results, results_weighting):
        teams_params = dict()
        home_adv_param = dict()

        #init gamma computations
        home_adv_param["gamma"] = 1
        home_adv_param["total_weighted_home_scored"] = 0
        for r in all_results:
            weight = results_weighting.weight(date, r.match.date)
            home_adv_param["total_weighted_home_scored"] += weight * r.home_goals

        # init param values to alpha=1 and beta =1
        for team in results_by_team.keys():
            teams_params[team] = {'alpha': 1., 'beta': 1., 'total_weighted_scored':0., 'total_weighted_conceded':0.,
                                  'nb_obs':0, 'sum_weight': 0.}

        # compute weighted scored and conceded goals
        for team, team_results in results_by_team.items():
            for r in team_results:
                weight = results_weighting.weight(date, r.match.date)
                scored = r.home_goals if r.home_team == team else r.away_goals
                conceded = r.home_goals if r.away_team == team else r.away_goals
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

        return teams_params, home_adv_param

    @staticmethod
    def param_local_optimum(date, results_by_team, all_results, teams_params, home_adv_param, results_weighting,
                            convergence_ratio):
        new_teams_params = dict(teams_params)

        for team in results_by_team.keys():
            new_teams_params[team]['alpha_tmp'] = 0.
            new_teams_params[team]['beta_tmp'] = 0.

        for team, results in results_by_team.items():
            for r in results:
                weight = results_weighting.weight(date, r.match.date)
                other_team = r.match.away_team if team == r.match.home_team else r.match.home_team
                gamma_atk = home_adv_param[team]['gamma'] if r.match.home_team == team else 1.
                gamma_def = 1. if r.match.home_team == team else home_adv_param[team]['gamma']
                new_teams_params[team]['alpha_tmp'] += weight * teams_params[other_team]['alpha'] * gamma_atk
                new_teams_params[team]['beta_tmp'] += weight * teams_params[other_team]['beta'] * gamma_def

        for r in all_results:
            weight = results_weighting.weight(date, r.match.date)
            home_adv_param["gamma_tmp"] += weight * teams_params[r.match.home_team]['alpha'] * \
                                           teams_params[r.match.away_team]['alpha']

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
            new_teams_params[team]["alpha"] = convergence_ratio * new_teams_params[team]["alpha"] * norm_alpha +\
                                              (1 - convergence_ratio) * teams_params[team]["alpha"]
            new_teams_params[team]["beta"] = convergence_ratio * new_teams_params[team]["beta"] * norm_beta +\
                                             (1 - convergence_ratio) * teams_params[team]["beta"]


        return new_teams_params

