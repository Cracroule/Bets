from bets_project.objects.bookmakersquotes import get_best_quote, quote_to_proba
from bets_project.objects.objects import EventOdds, Match, MatchResult
from math import log


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
    plikelihood_model, plikelihood_booky = 0., 0.
    nb_backtested_matches = 0
    distance_to_booky = 0.
    for match in all_matches_within_bet_range:
        if observed_team and match.home_team != observed_team and match.away_team != observed_team:
            continue

        best_booky_quotes = get_best_quote(match, all_relevant_quotes)

        match_params = param_estimator.get_match_parameters(match, all_results_before_end)
        prob_match_issues = model_match_outcomes.outcomes_probabilities(*match_params)
        bet_amounts = investment_strategy.get_investment_amounts(prob_match_issues, best_booky_quotes)

        booky_probas = quote_to_proba(best_booky_quotes)
        # norm_param = DiffGoalNormalDistrib.implied_param_from_proba(booky_probas)
        # poisson_param = GoalsPoissonDistrib.implied_param_from_proba(booky_probas)

        match_result = [r for r in manager.get_all(MatchResult) if r.match == match][0]
        match_gain = - sum(bet_amounts)
        diff = match_result.home_goals - match_result.away_goals
        victory_boolean = [diff > 0, diff == 0, diff < 0]
        for i in range(3):
            match_gain += bet_amounts[i] * best_booky_quotes[i] * victory_boolean[i]
            distance_to_booky += (booky_probas[i] - prob_match_issues[i]) ** 2.
            plikelihood_model += victory_boolean[i] * log(prob_match_issues[i])
            plikelihood_booky += victory_boolean[i] * log(booky_probas[i])

        total_gain += match_gain
        total_bet_amount += sum(bet_amounts)
        nb_backtested_matches += 1

        recap_bet_results.append({"result": match_result, "booky_quote": best_booky_quotes,
                                  "estimated_probas": prob_match_issues, "match_gain": match_gain})

    # plikelihood_model /= nb_backtested_matches
    # plikelihood_booky /= nb_backtested_matches

    print("nb backtested matchs:", nb_backtested_matches)
    print("total gain:", round(total_gain, 4), "  total bet amount:", round(total_bet_amount, 4),
          "   ratio:", round(total_gain / total_bet_amount, 4))
    print("distance_to_booky:", round(distance_to_booky, 4))
    print("plikelihood_model:", round(plikelihood_model, 4), "  plikelihood_booky:", round(plikelihood_booky, 4))
    return recap_bet_results










