from fuzzywuzzy import fuzz


class Anime:
    def __init__(self, name, year, localized_name=None):
        self.name = name
        self.year = year
        self.roma = localized_name

    def __eq__(self, other):
        if not isinstance(other, Anime):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def match(self, s):
        if self.roma is not None:
            return max(fuzz.ratio(self.name, s), fuzz.ratio(self.roma, s))
        else:
            return fuzz.ratio(self.name, s)
