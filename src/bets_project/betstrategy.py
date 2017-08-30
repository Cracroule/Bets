from bets_project.objects import Sport, Competition, CompetitionSeason, EventOdds, Event, \
    Team, Match, MatchResult, Bookmaker, BetObject
from math import sqrt
from bets_project.maths import cumulative_normal_distribution, ExponentialWeight, LinearWeight


""" look in past of each team in order to asset probability of issues W/D/A
This example of implementation assesses a typical goal difference for each team
And assumes that the expected goal difference of input match follow a normal distribution"""


def analyse_match(match, home_team_results, away_team_results):
    teams = match.home_team, match.away_team
    all_past_results = home_team_results, away_team_results

    # the below factor is used to reduce impact of old matchs compared to new ones
    # present_factor = 40. * 0.01
    # weight_manager = ExponentialWeight(present_factor)
    weight_manager = LinearWeight(365. * 2.)

    # the below constants are used to have an corrected estimation for
    # teams with short match history (from other divisions ?)
    min_matches_to_observe = 38.
    default_diff_when_no_history = -0.5

    # the below constant is the estimated std error for our goal diff
    sigma = 1.2

    # expected difference added to home team (supporter s help)
    home_goal_diff_advantage = 0.25

    # multiplier constant to apply on the sum of the assessed diff goals of each team (use 0.5 for average)
    diff_goal_factor = 0.7

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

            weight = weight_manager.weight(match.date, r.match.date)
            weighted_diff_sum += weight * goal_diff
            weights_sum += weight
            if weight:
                nb_observed_matches[i] += 1
        if weights_sum:
            estimated_diff = weighted_diff_sum / weights_sum
        else:
            estimated_diff = 0.
        corrected_estimated_diff = estimated_diff
        if nb_observed_matches[i] < min_matches_to_observe:
            corrected_estimated_diff *= nb_observed_matches[i] / min_matches_to_observe
            corrected_estimated_diff += default_diff_when_no_history * (min_matches_to_observe - nb_observed_matches[i])\
                                        / min_matches_to_observe
        estimated_diffs[i] = corrected_estimated_diff

    match_estimated_diff = diff_goal_factor * (estimated_diffs[0] - estimated_diffs[1]) + home_goal_diff_advantage

    p_home_d = cumulative_normal_distribution((-0.5 - match_estimated_diff) / sigma)
    p_home_v = 1 - cumulative_normal_distribution((0.5 - match_estimated_diff) / sigma)
    p_draw = cumulative_normal_distribution((0.5 - match_estimated_diff) / sigma) - cumulative_normal_distribution(
        (-0.5 - match_estimated_diff) / sigma)

    return p_home_v, p_draw, p_home_d


def get_investment_strategy(h_d_a_win_proba, booky_quotes, reversed=False):

    # we only bet if we think there is the below threshold in expected return (in percentage)
    bet_threshold = 0.05

    expected_gains = [h_d_a_win_proba[i] * booky_quotes[i] - 1. for i in range(3)]
    max_gain = max(expected_gains)
    if reversed:
        max_gain = min(expected_gains)
    bet_issue = expected_gains.index(max_gain)

    bet_amount = sqrt(abs(max_gain) * 100.) if abs(max_gain) > bet_threshold else 0.

    all_bet_amounts = [0., 0., 0.]
    all_bet_amounts[bet_issue] = bet_amount

    return all_bet_amounts


def away_investment_strategy(h_d_a_win_proba, booky_quotes):
    return [0., 0., 1.]


def get_best_quotes(match, quotes_list):
    events_list = Event('H'), Event('D'), Event('A')
    all_match_quotes = [q for q in quotes_list if q.match == match]
    all_quotes = [[q.value for q in all_match_quotes if q.event == ev] for ev in events_list]
    return [max(all_quotes[i]) for i in range(3)]


# TODO: make code more generic
def test_rpil(manager, d_start, d_end):
    all_matches = list(manager.get_all(Match))
    all_matches_within_bet_range = [m for m in all_matches if d_start <= m.date <= d_end]
    all_matches_within_bet_range.sort(key=lambda m: m.date)

    all_results = list(manager.get_all(MatchResult))
    all_results_before_end = [r for r in all_results if r.match.date <= d_end]
    all_results_before_end.sort(key=lambda r: r.match.date)

    favorite_booky = None
    # favorite_booky = Bookmaker('BbAv')
    all_quotes = list(manager.get_all(EventOdds))
    if favorite_booky:
        all_relevant_quotes = [q for q in all_quotes if
                               d_start <= q.match.date <= d_end and q.bookmaker == favorite_booky]
    else:
        all_relevant_quotes = [q for q in all_quotes if d_start <= q.match.date <= d_end]

    total_gain = 0.
    total_bet_amount = 0.
    for match in all_matches_within_bet_range:
        # if not (match.home_team.name == "Toulouse" and match.away_team.name == "St Etienne"):
        #     continue
        best_booky_quotes = get_best_quotes(match, all_relevant_quotes)
        # home_team_results = [r for r in all_results_before_end if r.match.date < match.date and
        #                      (match.home_team == r.match.home_team or match.home_team == r.m.away_team)]
        # away_team_results = [r for r in all_results_before_end if r.match.date < match.date and
        #                      (match.home_team == r.match.home_team or match.home_team == r.m.away_team)]
        home_team_results = list()
        away_team_results = list()
        for result in all_results_before_end:
            match_result = None
            # assumes all_results_before_end is sorted by date
            if result.match == match:
                match_result = result
                break
            if result.match.date > match.date:
                break
            if result.match.home_team == match.home_team or result.match.away_team == match.home_team:
                home_team_results.append(result)
            if result.match.home_team == match.away_team or result.match.away_team == match.away_team:
                away_team_results.append(result)

        prob_match_issues = analyse_match(match, home_team_results, away_team_results)
        # bet_amounts = get_investment_strategy(prob_match_issues, best_booky_quotes)
        bet_amounts = away_investment_strategy(prob_match_issues, best_booky_quotes)
        my_bet_quotes = [round(1./p, 3) for p in prob_match_issues]

        match_gain = - sum(bet_amounts)
        if match_result:
            diff = match_result.home_goals - match_result.away_goals
            victory_boolean = [diff > 0, diff == 0, diff < 0]
            for i in range(3):
                match_gain += bet_amounts[i] * best_booky_quotes[i] * victory_boolean[i]
            print(match_result, bet_amounts, match_gain, best_booky_quotes, my_bet_quotes)
            # print(match_result, best_booky_quotes, ' -->', my_bet_quotes)
        else:
            print(match, bet_amounts)

        total_gain += match_gain
        total_bet_amount += sum(bet_amounts)

    print("total gain:", total_gain)
    print("total bet amount:", total_bet_amount)













