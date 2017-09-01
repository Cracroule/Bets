from bets_project.objects import Sport, Competition, CompetitionSeason, EventOdds, Event, \
    Team, Match, MatchResult, Bookmaker
from bets_project.objectsmanager import ObjectsManager
from bets_project.investmentstrategy import GenericGainInvestStrategy, DummyHomeInvestStrategy,\
    DummyAwayInvestStrategy, DummyDrawInvestStrategy
from bets_project.matchoutcomesanalyser import DiffGoalAnalyser
from bets_project.matchoutcomesmodel import DiffGoalNormalDistrib, GoalsPoissonDistrib
from bets_project.backtesting import backtest
from bets_project.maths import LinearWeight, ExponentialWeight
from bets_project.bookmakersquotes import proba_to_quote, quote_to_proba, get_best_quote
# from bets_project.ma

from math import sqrt
import datetime, time


def validate_objects_consistency():
    manager = ObjectsManager()

    #sports creation
    football = Sport('Football')
    football_bis = Sport('Football')
    manager.push(football)

    #competition creation
    ligue_1 = Competition("Ligue 1", football)
    ligue_1_bis = Competition("Ligue 1", football_bis)
    ligue_2 = Competition("Ligue 2", football)

    assert(ligue_1.__dict__ == ligue_1_bis.__dict__)
    assert (ligue_1.__dict__ is not ligue_1_bis.__dict__)
    assert(ligue_1 == ligue_1_bis)
    assert(ligue_1 is not ligue_1_bis)
    assert(ligue_1 != ligue_2)
    manager.push(ligue_1)

    season_2016_2017 = CompetitionSeason("2016-2017", ligue_1)
    manager.push(season_2016_2017)

    all_competitions = list(manager.get_all(Competition))
    assert(str(all_competitions[0])=="Ligue 1")


def validate_manager_init():
    manager = ObjectsManager()
    manager.register_ligue_1()
    manager.register_odds_structure()
    initialized_classes = (Sport, Competition, Bookmaker, Event)
    for cl in initialized_classes:
        assert (cl in manager.cache.keys())
        assert (len(manager.cache[cl]) >= 1)


def validate_load_season_matches():
    manager = ObjectsManager()
    ligue_1 = manager.register_ligue_1()
    manager.register_odds_structure()
    ligue1_2015_2016 = CompetitionSeason("2015-2016", ligue_1)

    # data_dir = 'Bets/src/bets_project/data/'
    # data_dir = "/Users/cracr/Desktop/python_projects/Bets/src/bets_project/data/"
    data_dir = "/home/rpil/Desktop/perso/Bets/src/bets_project/data/"
    competition_label = ligue1_2015_2016.competition.name.lower().replace(' ', '').replace('_', '')
    season_label = ligue1_2015_2016.season.replace('/', '_').replace('-', '_')
    file = data_dir + competition_label + '_' + season_label + '.csv'
    manager.register_full_season_matches_from_csv(ligue1_2015_2016, file)

    assert(len(manager.get_all(Match)) == 380)
    assert(len(manager.get_all(Team)) == 20)


def validate_load_full_matches():
    manager = ObjectsManager()
    ligue_1 = manager.register_ligue_1()
    manager.register_odds_structure()

    # data_dir = 'Bets/src/bets_project/data/'
    # data_dir = "/Users/cracr/Desktop/python_projects/Bets/src/bets_project/data/"
    data_dir = "/home/rpil/Desktop/perso/Bets/src/bets_project/data/"

    s_labels_to_load = ('2009-2010', '2010-2011', '2011-2012', '2012-2013', '2013-2014', '2014-2015', '2015-2016')
    all_compet_season = [CompetitionSeason(s, ligue_1) for s in s_labels_to_load]
    for compet_season in all_compet_season:
        competition_label = compet_season.competition.name.lower().replace(' ', '').replace('_', '')
        season_label = compet_season.season.replace('/', '_').replace('-', '_')
        file = data_dir + competition_label + '_' + season_label + '.csv'
        manager.register_full_season_matches_from_csv(compet_season, file)

    assert (len(manager.get_all(Match)) == 380 * len(s_labels_to_load))
    assert (len(manager.get_all(MatchResult)) == 380 * len(s_labels_to_load))


def validate_normal_diff_model():
    epsilon_validation = 0.00001

    expected_goal_diff = 0.45
    sigma = 1.2
    outcomes_probas = DiffGoalNormalDistrib.outcomes_probabilities(expected_goal_diff, sigma)
    my_quote = proba_to_quote(outcomes_probas)
    my_quote_with_margin = proba_to_quote(outcomes_probas, margin=0.05)
    p_bis = quote_to_proba(my_quote)
    p_bis_bis = quote_to_proba(my_quote_with_margin)

    assert (all([abs(outcomes_probas[i] - p_bis[i]) < epsilon_validation for i in range(3)]))
    assert (all([abs(outcomes_probas[i] - p_bis_bis[i]) < epsilon_validation for i in range(3)]))

    init_params = expected_goal_diff, sigma
    implied_param = DiffGoalNormalDistrib.implied_param_from_proba(outcomes_probas)
    assert (all([abs(implied_param[i] - init_params[i]) < epsilon_validation for i in range(len(init_params))]))

    outcomes_probas_fair_match = DiffGoalNormalDistrib.outcomes_probabilities(0., sigma)
    assert(abs(outcomes_probas_fair_match[0] - outcomes_probas_fair_match[2]) < epsilon_validation)


def validate_poisson_goals_model():
    epsilon_validation = 0.00001

    shared_lambda = 1.3
    outcomes_probas_fair_match = GoalsPoissonDistrib.distrib_from_poisson_param(shared_lambda, shared_lambda)
    assert (abs(outcomes_probas_fair_match[0] - outcomes_probas_fair_match[2]) < epsilon_validation)

    lambda_param_1 = 2.0
    lambda_param_2 = 1.0
    outcomes_probas = GoalsPoissonDistrib.distrib_from_poisson_param(lambda_param_1, lambda_param_2)

    implied_param = GoalsPoissonDistrib.implied_param_from_proba(outcomes_probas)
    my_quote, my_quote_with_margin = proba_to_quote(outcomes_probas), proba_to_quote(outcomes_probas, margin=0.05)
    p_bis, p_bis_bis = quote_to_proba(my_quote), quote_to_proba(my_quote_with_margin)

    assert (all([abs(outcomes_probas[i] - p_bis[i]) < epsilon_validation for i in range(3)]))
    assert (all([abs(outcomes_probas[i] - p_bis_bis[i]) < epsilon_validation for i in range(3)]))


def test_strategy():
    manager = ObjectsManager()
    ligue_1 = manager.register_ligue_1()
    manager.register_odds_structure()

    # data_dir = "/Users/cracr/Desktop/python_projects/Bets/src/bets_project/data/"
    data_dir = "/home/rpil/Desktop/perso/Bets/src/bets_project/data/"

    s_labels_to_load = ('2009-2010', '2010-2011', '2011-2012', '2012-2013', '2013-2014', '2014-2015', '2015-2016')
    all_compet_season = [CompetitionSeason(s, ligue_1) for s in s_labels_to_load]
    for compet_season in all_compet_season:
        competition_label = compet_season.competition.name.lower().replace(' ', '').replace('_', '')
        season_label = compet_season.season.replace('/', '_').replace('-', '_')
        file = data_dir + competition_label + '_' + season_label + '.csv'
        manager.register_full_season_matches_from_csv(compet_season, file)

    # let s focus on 1rst game of ligue1
    d_start = datetime.datetime.strptime("06-08-2013", '%d-%m-%Y').date()
    d_end = datetime.datetime.strptime("18-06-2014", '%d-%m-%Y').date()

    sigma = 1.2
    home_goal_diff_advantage = 0.25
    min_expected_results = 38
    no_history_penalty = -0.5
    diff_goal_aggregation_multiplier = 0.7
    results_weighting = LinearWeight(365 * 2.)
    outcomes_model = DiffGoalNormalDistrib()
    match_outcome_analyser = DiffGoalAnalyser(sigma, home_goal_diff_advantage, min_expected_results, no_history_penalty,
                                              diff_goal_aggregation_multiplier,results_weighting, outcomes_model)

    # investment_strategy = DummyDrawInvestStrategy()
    investment_gain_threshold = 0.05
    fct_of_gain = sqrt
    investment_strategy = GenericGainInvestStrategy(investment_gain_threshold, fct_of_gain)
    # backtest(manager, d_start, d_end, match_outcome_analyser, investment_strategy, observed_team_name="Paris SG")
    # backtest(manager, d_start, d_end, match_outcome_analyser, investment_strategy, favorite_bookmaker=Bookmaker('BbAv'),
    #          observed_team="Paris SG")
    backtest(manager, d_start, d_end, match_outcome_analyser, investment_strategy)
    # backtest(manager, d_start, d_end, match_outcome_analyser, investment_strategy, favorite_bookmaker=Bookmaker('BbAv'))


def main():
    tps1 = time.clock()

    validate_objects_consistency()
    validate_manager_init()
    validate_load_season_matches()
    validate_load_full_matches()
    validate_normal_diff_model()
    validate_poisson_goals_model()

    test_strategy()

    tps2 = time.clock()

    print(' all is fine', '(execution time is', tps2 - tps1, ')')


if __name__ == '__main__':
    main()