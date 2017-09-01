class ResultsAnalysis(object):

    def __init__(self):
        raise NotImplementedError('attempt to instantiate abstract class ResultsAnalysis')

    def analyse(self, **kwargs):
        raise NotImplementedError()


class BasicGenericAnalysis(object):

    def __init__(self, results_fct=None):
        self.results_fct = results_fct

    # TODO: complete analysis with home / away differentiation
    def analyse_team_results(self, team, team_results, nb_max_observations=None):
        all_results = sorted([r for r in team_results if team in (r.match.home_team, r.match.away_team)],
                             key=lambda x: x.match.date)
        if nb_max_observations and len(all_results) > nb_max_observations:
            all_results = all_results[len(all_results) - nb_max_observations:]

        analysis = {'W': 0, 'D': 0, 'L': 0, 'conceded': 0, 'scored': 0, 'played': 0}
        for r in all_results:
            scored, conceded = (r.home_goals, r.away_goals) if r.match.home_team == team else (r.away_goals, r.home_goals)
            if scored > conceded:
                analysis['W'] += 1
            elif scored < conceded:
                analysis['L'] += 1
            else:
                analysis['D'] += 1
            if self.results_fct:
                if 'fct_outputs' not in analysis.keys(): analysis['fct_outputs'] = list()
                analysis['fct_outputs'].append(self.results_fct(r, team))
            analysis['scored'] += scored
            analysis['conceded'] += conceded
            analysis['played'] += 1
        return analysis