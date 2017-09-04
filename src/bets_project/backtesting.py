from bets_project.objects import Sport, Competition, CompetitionSeason, EventOdds, Event, \
    Team, Match, MatchResult, Bookmaker, BetObject
from math import sqrt
from bets_project.maths import cumulative_normal_distribution, ExponentialWeight, LinearWeight
from bets_project.matchoutcomesanalyser import DiffGoalAnalyser
from bets_project.investmentstrategy import DummyAwayInvestStrategy, DummyDrawInvestStrategy, DummyHomeInvestStrategy, \
    GenericGainInvestStrategy
from bets_project.bookmakersquotes import get_best_quote, proba_to_quote, quote_to_proba
from bets_project.matchoutcomesmodel import GoalsPoissonDistrib, DiffGoalNormalDistrib
from bets_project.resultsanalysis import BasicGenericAnalysis


# # TODO delete here (has been copied in ModelParamEstimation)
# def get_relative_results_history(match, iterable_results, nb_max_results=None, max_days=None):
#     home_team_results, away_team_results = list(), list()
#     match_result = None
#     for result in iterable_results:
#
#         if result.match == match:
#             match_result = result
#             continue
#
#         if result.match == match or result.match.date > match.date:
#             continue
#
#         if max_days:
#             time_to_result = match.date - result.match.date
#             if time_to_result.days > max_days:
#                 continue
#
#         if result.match.home_team == match.home_team or result.match.away_team == match.home_team:
#             home_team_results.append(result)
#         if result.match.home_team == match.away_team or result.match.away_team == match.away_team:
#             away_team_results.append(result)
#
#     home_team_results.sort(key=lambda r: r.match.date)
#     away_team_results.sort(key=lambda r: r.match.date)
#
#     if nb_max_results and len(home_team_results) > nb_max_results:
#         home_team_results = home_team_results[len(home_team_results) - nb_max_results:]
#     if nb_max_results and len(away_team_results) > nb_max_results:
#         away_team_results = away_team_results[len(away_team_results) - nb_max_results:]
#
#     return home_team_results, away_team_results, match_result
#
#
# # TODO: make code more generic
# def backtest(manager, d_start, d_end, match_outcome_analyser, investment_strategy, favorite_bookmaker=None,
#              observed_team_name=None):
#
#     all_matches = list(manager.get_all(Match))
#     all_matches_within_bet_range = [m for m in all_matches if d_start <= m.date <= d_end]
#     all_matches_within_bet_range.sort(key=lambda m: m.date)
#
#     all_results = list(manager.get_all(MatchResult))
#     all_results_before_end = [r for r in all_results if r.match.date <= d_end]
#     all_results_before_end.sort(key=lambda r: r.match.date)
#
#     all_quotes = list(manager.get_all(EventOdds))
#     if favorite_bookmaker:
#         all_relevant_quotes = [q for q in all_quotes if
#                                d_start <= q.match.date <= d_end and q.bookmaker == favorite_bookmaker]
#     else:
#         all_relevant_quotes = [q for q in all_quotes if d_start <= q.match.date <= d_end]
#
#     total_gain = 0.
#     total_bet_amount = 0.
#     for match in all_matches_within_bet_range:
#         if observed_team_name and match.home_team.name != observed_team_name and match.away_team.name != observed_team_name:
#             continue
#         best_booky_quotes = get_best_quote(match, all_relevant_quotes)
#         home_team_results, away_team_results, match_result = get_relative_results_history(match, all_results_before_end)
#
#         prob_match_issues = match_outcome_analyser.analyse(match, home_team_results, away_team_results)
#         bet_amounts = investment_strategy.get_investment_amounts(prob_match_issues, best_booky_quotes)
#
#         # bet_amounts = quote_to_proba(best_booky_quotes)
#         # bet_amounts = [0, 1, 0]
#
#         # tests, to be deleted
#         booky_probas = quote_to_proba(best_booky_quotes)
#         norm_param = DiffGoalNormalDistrib.implied_param_from_proba(booky_probas)
#         poisson_param = GoalsPoissonDistrib.implied_param_from_proba(booky_probas)
#         display = [[round(e, 3) for e in d] for d in (booky_probas, norm_param, poisson_param)]
#
#         match_gain = - sum(bet_amounts)
#         if match_result:
#             diff = match_result.home_goals - match_result.away_goals
#             victory_boolean = [diff > 0, diff == 0, diff < 0]
#             for i in range(3):
#                 match_gain += bet_amounts[i] * best_booky_quotes[i] * victory_boolean[i]
#             print(match_result, best_booky_quotes, ' -->', display[1:])
#         else:
#             print(match, bet_amounts)
#
#         total_gain += match_gain
#         total_bet_amount += sum(bet_amounts)
#
#     print("total gain:", total_gain)
#     print("total bet amount:", total_bet_amount)
#     print("ratio:", round(total_gain / total_bet_amount, 4))


def backtest_strategy(manager, d_start, d_end, param_estimator, model_match_outcomes, investment_strategy,
              favorite_bookmaker=None, observed_team=None):

    all_matches = list(manager.get_all(Match))
    all_matches_within_bet_range = [m for m in all_matches if d_start <= m.date <= d_end]
    all_matches_within_bet_range.sort(key=lambda m: m.date)

    all_results = list(manager.get_all(MatchResult))
    all_results_before_end = [r for r in all_results if r.match.date <= d_end]
    all_results_before_end.sort(key=lambda r: r.match.date)

    all_quotes = list(manager.get_all(EventOdds))
    if favorite_bookmaker:
        all_relevant_quotes = [q for q in all_quotes if
                               d_start <= q.match.date <= d_end and q.bookmaker == favorite_bookmaker]
    else:
        all_relevant_quotes = [q for q in all_quotes if d_start <= q.match.date <= d_end]

    total_gain = 0.
    total_bet_amount = 0.
    recap_bet_results = list()
    for match in all_matches_within_bet_range:
        if observed_team and match.home_team != observed_team and match.away_team != observed_team:
            continue

        best_booky_quotes = get_best_quote(match, all_relevant_quotes)

        match_params = param_estimator.get_match_parameters(match, all_results_before_end)
        prob_match_issues = model_match_outcomes.distrib_from_poisson_param(*match_params)
        bet_amounts = investment_strategy.get_investment_amounts(prob_match_issues, best_booky_quotes)

        # booky_probas = quote_to_proba(best_booky_quotes)
        # norm_param = DiffGoalNormalDistrib.implied_param_from_proba(booky_probas)
        # poisson_param = GoalsPoissonDistrib.implied_param_from_proba(booky_probas)

        match_result = [r for r in manager.get_all(MatchResult) if r.match == match][0]
        match_gain = - sum(bet_amounts)
        diff = match_result.home_goals - match_result.away_goals
        victory_boolean = [diff > 0, diff == 0, diff < 0]
        for i in range(3):
            match_gain += bet_amounts[i] * best_booky_quotes[i] * victory_boolean[i]

        total_gain += match_gain
        total_bet_amount += sum(bet_amounts)

        recap_bet_results.append({"result": match_result, "booky_quote": best_booky_quotes,
                                  "estimated_probas": prob_match_issues, "match_gain": match_gain})

    print("total gain:", total_gain)
    print("total bet amount:", total_bet_amount)
    print("ratio:", round(total_gain / total_bet_amount, 4))
    return recap_bet_results










