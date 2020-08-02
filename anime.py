def triples(s):
    l = [c for c in s.lower() if c in string.ascii_lowercase + string.digits]
    return {"".join(l[i:i+3]) for i in range(0, len(l)-2)}

def trigram(x, y):
    return len(triples(x) & triples(y)) / len(triples(x) | triples(y))


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
            return max(trigram(self.name, s), trigram(self.roma, s))
        else:
            return trigram(self.name, s)
