from bets_project.Objects import Sport, Competition, CompetitionSeason


class ObjectsManager(object):

    def __init__(self):
        self.cache = dict()

    def push(self, obj):
        obj_cl = obj.__class__
        if obj_cl not in self.cache.keys():
            self.cache[obj_cl] = set()
        self.cache[obj_cl].add(obj)

