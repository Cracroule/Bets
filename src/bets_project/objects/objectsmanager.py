from bets_project.objects.objects import Sport, Competition, CompetitionSeason, EventOdds, Event, \
    Team, Match, MatchResult, Bookmaker, BetObject
import inspect
import datetime
import csv


class ObjectsManager(object):

    def __init__(self):
        self.cache = dict()

    def push(self, obj, allow_iterable=True):
        if allow_iterable:
            try:
                for o in obj:
                    self.push(o, allow_iterable=False)
            except TypeError:
                pass
        obj_cl = obj.__class__
        if obj_cl not in self.cache.keys():
            self.cache[obj_cl] = set()
        self.cache[obj_cl].add(obj)

    def get_all(self, cl):
        if not issubclass(cl, BetObject):
            return Exception("get_all should be called with an arg of type BetObject")
        if cl in self.cache:
            return self.cache[cl]
        return []

    # return the already instanciated object if existing, else push it and return itself
    #needed ?
    # def get_or_create(self, obj):
    #     obj_cl = obj.__class__
    #     if obj_cl not in self.cache.keys():
    #         self.cache[obj_cl] = set()
    #         self.cache[obj_cl].add(obj)
    #         return obj
    #     else:
    #         if obj in self.cache[obj_cl]:
    #             return

    def init(self):
        self.register_ligue_1()
        self.register_odds_structure()

    def register_ligue_1(self):
        # sports creation
        football = Sport('Football')
        self.push(football)

        # competition creation
        ligue_1 = Competition("Ligue 1", football)
        self.push(ligue_1)

        return ligue_1

    def register_odds_structure(self):

        odd_event_list = [("H", "Home Win Odds"),
                          ("D", "Draw Odds"),
                          ("A", "Away Win Odds"), ]

        for e in odd_event_list:
            event = Event(label=e[0], description=e[1])
            self.push(event)

        bookmakers_list = [('Bet365', 'B365'),
                           ('Blue Square', 'BS'),
                           ('Bet and Win', 'BW'),
                           ('Gamebookers', 'GB'),
                           ('Interwetten', 'IW'),
                           ('Ladbrokes', 'LB'),
                           ('Pinnacle', 'PS'),
                           ('Sporting', 'SO'),
                           ('Sportingbet', 'SB'),
                           ('Stan James', 'SJ'),
                           ('Stanleybet', 'SY'),
                           ('VC Bet', 'VC'),
                           ('William Hill', 'WH'),
                           ('BetBrain average', 'BbAv'), ]

        self.push((Bookmaker(label=e[1], full_name=e[0]) for e in bookmakers_list))
        # for bkm in bookmakers_list:
        #     bookmaker = Bookmaker(name=bkm[0], label=bkm[1])
        #     self.push(bookmaker)

    """ Create and register a match. If necessary, creates involved teams
    Input is a dict with following keys:
    - HomeTeam
    - AwayTeam
    - season
    - Date
    - FTHG
    - FTAG
    """
    # stats might be saved here as well, ToBeImplemented later on
    # TODO: implement stats
    def register_match(self, input_dict):
        home_team = Team(name=input_dict['HomeTeam'])
        away_team = Team(name=input_dict['AwayTeam'])
        self.push(home_team)
        self.push(away_team)

        match_date = datetime.datetime.strptime(input_dict['Date'], '%d/%m/%y').date()
        match = Match(competition_season=input_dict['competition_season'], date=match_date, home_team=home_team,
                      away_team=away_team)
        match_result = MatchResult(match, int(input_dict['FTHG']), int(input_dict['FTAG']))
        self.push(match)
        self.push(match_result)

        # save odds
        # all_bkmk = ['BbAv'] # not interested by other ones for now
        # all_bkmk = (bkm for bkm in self.get_all(Bookmaker) if bkm.label == 'BbAv')
        all_bkmk = list(self.get_all(Bookmaker))
        for bkmk in all_bkmk:
            odd_labels = [bkmk.label + end_label for end_label in ('H', 'D', 'A')]
            for odd_label in odd_labels:
                if odd_label in input_dict.keys():
                    try:
                        booky_quote = float(input_dict[odd_label])
                    except:
                        continue
                    event = Event(odd_label[-1])
                    event_odds = EventOdds(bkmk, match, event, value=booky_quote)
                    self.push(event_odds)

    def register_full_season_matches_from_csv(self, competition_season, file):
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row_dict in reader:
                row_dict['competition_season'] = competition_season
                self.register_match(row_dict)

