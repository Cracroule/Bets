# from datetime import datetime


class BetObject(object):

    def __ne__(self, other):
        return not self.__eq__(other)


class Sport(BetObject):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)


class Competition(BetObject):

    def __init__(self, name, sport):
        self.name = name
        self.sport = sport

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash((self.name, self.sport))


class CompetitionSeason(BetObject):

    def __init__(self, season, competition):
        self.season = season
        self.competition = competition

    def __str__(self):
        return '%s %s' % (str(self.competition), self.season)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.season == other.season and self.competition == other.competition
        return NotImplemented

    def __hash__(self):
        return hash((self.season, self.competition))


class Match(BetObject):

    def __init__(self, competition_season, date, home_team, away_team):
        self.competition_season = competition_season
        self.date = date
        self.home_team = home_team
        self.away_team = away_team

    def __str__(self):
        return '%s vs %s %s' % (str(self.home_team), str(self.away_team), self.date)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.competition_season == other.competition_season and self.date == other.date and \
                   self.home_team == other.home_team and self.away_team == other.away_team
        return NotImplemented

    def __hash__(self):
        return hash((self.competition_season, self.date, self.home_team, self.away_team))


class MatchResult(BetObject):

    def __init__(self, match, home_goals, away_goals):
        self.match = match
        self.home_goals = home_goals
        self.away_goals = away_goals


    def __str__(self):
        return '%s: %d - %d' % (str(self.match), int(self.home_goals), int(self.away_goals))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.match == other.match
        return NotImplemented

    def __hash__(self):
        return hash((self.home_goals, self.away_goals, self.match))


class Team(BetObject):

    # should it be defined by a sport as well ?
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __hash__(self):
        return hash(self.name)


class Bookmaker(BetObject):

    def __init__(self, name, label):
        self.name = name
        self.label = label

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.label == other.label
        return NotImplemented

    def __hash__(self):
        return hash((self.name, self.label))


class Event(BetObject):

    LABEL_LIST = ['H', 'D', 'A']

    def __init__(self, label, description=None):
        self.label = label
        self.description = description

    def __str__(self):
        return self.description

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.label == other.label
        return NotImplemented

    def __hash__(self):
        return hash(self.label)


class EventOdds(BetObject):

    def __init__(self, bookmaker, match, event, value):
        self.bookmaker = bookmaker
        self.match = match
        self.event = event
        self.value = value

    def __str__(self):
        return '%s for %s by %s = %s' % (self.event, self.match, self.bookmaker, self.value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.match == other.match and self.event == other.event and self.bookmaker == other.bookmaker
        return NotImplemented

    def __hash__(self):
        return hash((self.match, self.event, self.bookmaker))
