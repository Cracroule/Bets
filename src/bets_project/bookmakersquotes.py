from bets_project.objects import EventOdds, Event, Team, Match, Bookmaker


def get_best_quote(match, quotes_list):
    events_list = Event('H'), Event('D'), Event('A')
    all_match_quotes = [q for q in quotes_list if q.match == match]
    all_quotes = [[q.value for q in all_match_quotes if q.event == ev] for ev in events_list]
    return [max(all_quotes[i]) for i in range(3)]


def quote_to_proba(bookmaker_quote_list):
    proba_with_booky_margin = [1./q for q in bookmaker_quote_list]
    sum_proba_with_margin = sum(proba_with_booky_margin)
    return [p/sum_proba_with_margin for p in proba_with_booky_margin]


def proba_to_quote(proba_list, margin=0.):
    return [1./(p * (1. + margin)) for p in proba_list]
