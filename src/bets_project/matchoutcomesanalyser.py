# from bets_project.objects import Sport, Competition, CompetitionSeason, EventOdds, Event, \
#     Team, Match, MatchResult, Bookmaker, BetObject
# import datetime
from bets_project.maths import cumulative_normal_distribution, ExponentialWeight, LinearWeight


class MatchOutcomesAnalyser(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class MatchOutcomeAnalyse')

    def analyse(self, **kwargs):
        raise NotImplementedError()

#
# """ look in past of each team in order to asset probability of issues W/D/A
# This example of implementation assesses a typical goal difference for each team
# And assumes that the expected goal difference of input match follow a normal distribution"""
#


class DiffGoalAnalyser(MatchOutcomesAnalyser):

    def __init__(self, diff_goal_std_uncertainty, home_goal_diff_advantage, min_expected_results, no_history_penalty,
                 diff_goal_aggregation_multiplier, results_weighting, outcomes_model):
        self.sigma = diff_goal_std_uncertainty
        self.home_goal_diff_advantage = home_goal_diff_advantage
        self.min_expected_results = min_expected_results
        self.no_history_penalty = no_history_penalty
        self.results_weighting = results_weighting
        self.diff_goal_aggregation_multiplier = diff_goal_aggregation_multiplier
        self.outcomes_model = outcomes_model

    def analyse(self, match, home_past_results, away_past_results):
        teams = match.home_team, match.away_team
        all_past_results = home_past_results, away_past_results
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

        outcomes_probas = self.outcomes_model.outcomes_probabilities(match_estimated_diff, self.sigma)
        return outcomes_probas
