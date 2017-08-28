from bets_project.Objects import Sport, CompetitionSeason, Competition
from bets_project.ObjectsManager import ObjectsManager


def test_objects_consistency():
    manager = ObjectsManager()

    #sports creation
    football = Sport('Football')
    football_bis = Sport('Football')
    manager.push(football)

    # #competition creation
    ligue_1 = Competition("Ligue 1", football)
    ligue_1_bis = Competition("Ligue 1", football_bis)
    ligue_2 = Competition("Ligue 2", football)
    # print(ligue_1.__dict__)
    # print(ligue_1_bis.__dict__)
    assert(ligue_1.__dict__ == ligue_1_bis.__dict__)
    assert (ligue_1.__dict__ is not ligue_1_bis.__dict__)
    assert(ligue_1 == ligue_1_bis)
    assert(ligue_1 is not ligue_1_bis)
    assert(ligue_1 != ligue_2)
    manager.push(ligue_1)

    # #competition_season creation
    season_2016_2017 = CompetitionSeason("2016-2017", ligue_1)
    manager.push(season_2016_2017)
    manager.push(season_2016_2017)

    # print(manager.cache[season_2016_2017.__class__])
    # print(len(manager.cache[season_2016_2017.__class__]))


def main():
    test_objects_consistency()


if __name__ == '__main__':
    main()