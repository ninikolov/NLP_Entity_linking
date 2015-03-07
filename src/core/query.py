# -*- coding: utf-8 -*-

class SearchQuery(object):
    def __init__(self, search_string):
        self.search_string = search_string
        self.array = search_string.split()
        self.search_matches = []

    def add_match(self, match):
        # match: SearchMatch
        self.search_matches.append(match)

    def rank_matches(self):
        pass

    def __repr__(self):
        #return "<SearchQuery: %s>" % self.search_string
        return self.search_string

    def choose_best_entities(self):
        """
        TODO: Figure out a better way to do this
        """
        best_entities = {}
        for match in self.search_matches:
            substring, entity = match.choose_best_match()
            best_entities[substring] = entity
        return best_entities

    def get_search_string(self):
        return self.search_string

    def visualize(self):
        print("="*40, "\n Query: \"" + self.search_string, "\"\nEntities:\n")
        for substr, entity in self.choose_best_entities().items():
            print("Text: "+substr + " | ", entity)
        print("="*40 + "\n")

class SearchMatch(object):
    def __init__(self, position, entities, substring):
        self.substring = substring
        self.position = position
        self.entities = entities

    def __repr__(self):
        return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, self.entities)

    def choose_best_match(self):
        """
        """
        return self.substring, self.entities[0]

class Entity(object):
    def __init__(self, link, probability):
        self.link = link
        self.probability = float(probability)

    def __repr__(self):
        return "<Entity: %s %f>" % (self.link, self.probability)