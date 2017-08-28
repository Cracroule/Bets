from bets_project.Objects import Sport, Competition, CompetitionSeason
import inspect


class ObjectsManager(object):

    def __init__(self):
        self.cache = dict()

    def push(self, obj, allow_iterable=True):
        try:
            for o in obj:
                self.push(o, allow_iterable=False)
        except:
            pass
        obj_cl = obj.__class__
        if obj_cl not in self.cache.keys():
            self.cache[obj_cl] = set()
        self.cache[obj_cl].add(obj)

    def get_all(self, cl):
        if not inspect.isclass(cl):
            return Exception("get_all should be called with an arg of type class")
        if cl in self.cache:
            return self.cache[cl]
        return []
