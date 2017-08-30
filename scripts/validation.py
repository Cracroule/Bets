from bets_project.objects import Sport, Competition, CompetitionSeason, EventOdds, Event, \
    Team, Match, MatchResult, Bookmaker
from bets_project.betstrategy import test_rpil
from bets_project.objectsmanager import ObjectsManager
import datetime


def test_objects_consistency():
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


def test_manager_init():
    manager = ObjectsManager()
    manager.register_ligue_1()
    manager.register_odds_structure()
    initialized_classes = (Sport, Competition, Bookmaker, Event)
    for cl in initialized_classes:
        assert (cl in manager.cache.keys())
        assert (len(manager.cache[cl]) >= 1)


def test_load_season_matches():
    manager = ObjectsManager()
    ligue_1 = manager.register_ligue_1()
    manager.register_odds_structure()
    ligue1_2015_2016 = CompetitionSeason("2015-2016", ligue_1)

    # data_dir = 'Bets/src/bets_project/data/'
    data_dir = "/Users/cracr/Desktop/python_projects/Bets/src/bets_project/data/"
    competition_label = ligue1_2015_2016.competition.name.lower().replace(' ', '').replace('_', '')
    season_label = ligue1_2015_2016.season.replace('/', '_').replace('-', '_')
    file = data_dir + competition_label + '_' + season_label + '.csv'
    manager.register_full_season_matches_from_csv(ligue1_2015_2016, file)

    assert(len(manager.get_all(Match)) == 380)
    assert(len(manager.get_all(Team)) == 20)


def test_load_full_matches():
    manager = ObjectsManager()
    ligue_1 = manager.register_ligue_1()
    manager.register_odds_structure()

    # data_dir = 'Bets/src/bets_project/data/'
    data_dir = "/Users/cracr/Desktop/python_projects/Bets/src/bets_project/data/"

    s_labels_to_load = ('2009-2010', '2010-2011', '2011-2012', '2012-2013', '2013-2014', '2014-2015', '2015-2016')
    all_compet_season = [CompetitionSeason(s, ligue_1) for s in s_labels_to_load]
    for compet_season in all_compet_season:
        competition_label = compet_season.competition.name.lower().replace(' ', '').replace('_', '')
        season_label = compet_season.season.replace('/', '_').replace('-', '_')
        file = data_dir + competition_label + '_' + season_label + '.csv'
        manager.register_full_season_matches_from_csv(compet_season, file)

    assert (len(manager.get_all(Match)) == 380 * len(s_labels_to_load))
    assert (len(manager.get_all(MatchResult)) == 380 * len(s_labels_to_load))


def test_strategy():
    manager = ObjectsManager()
    ligue_1 = manager.register_ligue_1()
    manager.register_odds_structure()

    data_dir = "/Users/cracr/Desktop/python_projects/Bets/src/bets_project/data/"

    s_labels_to_load = ('2009-2010', '2010-2011', '2011-2012', '2012-2013', '2013-2014', '2014-2015', '2015-2016')
    all_compet_season = [CompetitionSeason(s, ligue_1) for s in s_labels_to_load]
    for compet_season in all_compet_season:
        competition_label = compet_season.competition.name.lower().replace(' ', '').replace('_', '')
        season_label = compet_season.season.replace('/', '_').replace('-', '_')
        file = data_dir + competition_label + '_' + season_label + '.csv'
        manager.register_full_season_matches_from_csv(compet_season, file)

    # let s focus on 1rst game of ligue1
    d_start = datetime.datetime.strptime("06-08-2015", '%d-%m-%Y').date()
    d_end = datetime.datetime.strptime("18-06-2016", '%d-%m-%Y').date()

    test_rpil(manager, d_start, d_end)


def main():
    test_objects_consistency()
    test_manager_init()
    # test_load_season_matches()
    # test_load_full_matches()
    test_strategy()
    print('all is fine')


if __name__ == '__main__':
    main()