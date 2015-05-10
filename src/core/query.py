# -*- coding: utf-8 -*-
from urllib.request import unquote

import wikipedia
from wikipedia import DisambiguationError
import enchant

from core.helper import TermColor


spell = enchant.Dict("en_US")
# "TP-strict", "TP-relaxed", "FP", "FN"
EXPORT_COLORS = {
    "FN": "blue",
    "FP": "red",
    "TP-relaxed": "yellow",
    "TP-strict": "green"
}


class SearchSession(list):
    # store session id and otherwise behave like a list
    # that contains all the search queries belonging to a
    # specific session
    def __init__(self, id_):
        self.session_id = id_

    def __repr__(self):
        return str("<SearchSession: " + self.session_id + ": "
                   + super().__repr__() + ">")


class SearchQuery(object):
    def __init__(self, search_string, session=None):
        self.search_string = search_string
        # self.array = re.findall(r"[\w]+", search_string)
        self.array = self.search_string.split()
        self.search_matches = []
        self.true_entities = []
        self.session = session

    def add_match(self, match):
        # match: SearchMatch
        self.search_matches.append(match)

    def spell_check(self):
        for w in self.array:
            if not spell.check(w):
                sug = spell.suggest(w)
                try:
                    w = sug[0]
                except IndexError:
                    pass
                    # print(spell.suggest(w))

    def rank_matches(self):
        pass

    def __repr__(self):
        # return "<SearchQuery: %s>" % self.search_string
        return self.search_string

    def get_chosen_entities(self):
        return [m.entities[m.chosen_entity] for m in self.search_matches if m.entities and m.chosen_entity >= 0]

    def clean(self):
        for match in self.search_matches:
            match.clean()


    # def choose_best_entities(self):
    # """
    # TODO: Figure out a better way to do this
    #     """
    #     best_entities = {}
    #     for match in self.search_matches:
    #         substring, entity = match.choose_best_match()
    #         best_entities[substring] = entity
    #     return best_entities

    def get_search_string(self):
        return self.search_string

    def visualize(self):

        colors = {'TP-strict': TermColor.GREEN, 'TP-relaxed': TermColor.YELLOW, 'FP': TermColor.RED,
                  'FP-Corresponding_true_entity': TermColor.RED, 'FN': TermColor.BLUE, "": TermColor.CYAN}

        #The query is normally visualised once. But if some matches are overlapping, we will need to show
        #the string more than once so that all the matches can be seen.
        visu = []  # search string visalization
        index_ssv = 0  #index search string vizualization

        search_matches_copy = list(self.search_matches)
        while len(search_matches_copy) > 0:
            word_pointer = 0
            visu.append("")
            while word_pointer < len(self.array):
                #in this loop we go through the words in the query array and look if there are corresponding matches
                match_exists = False
                for match in search_matches_copy:
                    if (not match.rating):
                        search_matches_copy.remove(match)
                        break  #This should normally not happen. However it seems that it happens in the case where
                        #the xml is incomplete (check dev-set "New York American Girl dolls cost"). TODO : Look into that.
                    if match.position == word_pointer:
                        #we check the starting position of the match.
                        # followed by an assert : check if the words (not ony position) coincide
                        try:
                            assert (match.substring.split()[0] == self.array[word_pointer])
                        except AssertionError:
                            print(match.substring.split()[0], "|", self.array[word_pointer])
                            # raise  AssertionError
                        visu[index_ssv] += "{0}{1}{2} ".format(
                            colors[match.rating], match.substring, TermColor.END)
                        word_pointer += match.word_count
                        if (word_pointer < len(self.array)):
                            visu[index_ssv] += "| "  #Separate the matches
                        match_exists = True
                        search_matches_copy.remove(match)
                        break
                if (not match_exists):
                    #this word corresponds to no match, so we write it in white
                    visu[index_ssv] += self.array[word_pointer] + " "
                    word_pointer += 1
            #now, some (overlapping) matches may have been overlooked. in this case the search_matches_copy will
            #not be empty here so it will go through the while loop again. 
            index_ssv += 1

        print("{:=^80}\nQuery: {:}{:}{:}\n".format("", TermColor.BOLD,
                                                   self.search_string, TermColor.END, ""))
        print(" |&| ".join(visu))
        for match in self.search_matches:
            if match.get_chosen_entity():
                print("{0}{1:<25} | {2}{3}".format(colors[match.rating],
                                                   match.substring, match.get_chosen_entity(), TermColor.END))

        first = True
        for true_match in self.true_entities:
            if (not true_match.rating in ("TP-strict", "TP-relaxed")):
                if (first):
                    print("Missed entities:")
                first = False
                print("{0}{1:<25} | {2}{3}".format(colors[true_match.rating],
                                                   true_match.substring, true_match.entities[0], TermColor.END))
        print("All true entities:", self.true_entities)
        print("-" * 80 + "\n")

    def add_to_export(self, exporter):
        from collections import OrderedDict

        search = OrderedDict()
        for a in self.array:
            search[a] = {}

        exporter.append_row(OrderedDict())
        exporter.append_row(search)

        res = OrderedDict()

        m = list(self.search_matches)
        m.sort(key=lambda s: s.position)

        for a in m:
            ent = a.get_chosen_entity()
            if ent:
                res[ent.link] = {
                    "link": "http://en.wikipedia.org/wiki/" + ent.link,
                    "span": a.word_count,
                    "bg": EXPORT_COLORS[a.rating]
                }

        exporter.append_row(res)
        true_res = OrderedDict()
        m = list(self.true_entities)
        m.sort(key=lambda s: s.position)
        for t in m:
            # print("True Ent: ", t)
            ent = t.get_chosen_entity()
            # print(ent.link, t.word_count, t.position)
            if ent:
                true_res[ent.link] = {
                    "link": "http://en.wikipedia.org/wiki/" + ent.link,
                    "span": t.word_count
                }

        exporter.append_row(true_res)


class SearchMatch(object):
    def __init__(self, position, word_count, entities, substring):
        self.substring = substring
        self.position = position
        self.word_count = word_count
        self.entities = entities
        self.chosen_entity = -1  # a positive number indicates array index
        # of chosen entity, -1 == no entity chosen
        self.rating = ""  # "TP-strict", "TP-relaxed", "FP", "FN"

    def __repr__(self):
        # try:
        return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, [e for e in self.entities])
        # except IndexError:
        # return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, [e for e in self.entities])

    def get_chosen_entity(self):
        if self.entities and self.chosen_entity >= 0:
            return self.entities[self.chosen_entity]
        else:
            return None

    def get_entities_limit(self, size_limit=5, prob_limit=None):
        """
        """
        if prob_limit:
            ents = [e for e in self.entities if e.probability >= prob_limit]
        else:
            ents = self.entities
        if not size_limit or len(ents) <= size_limit:
            return ents
        else:
            return ents[:size_limit]

    def clean(self):
        self.entities = [self.entities[self.chosen_entity]]
        self.chosen_entity = 0 if self.chosen_entity > -1 else -1

        # def choose_best_match(self):
        # """
        # """
        # return self.substring, self.entities[0]


entity_correction_mapper = {}


class Entity(object):
    def __init__(self, link, probability):
        self.link = link
        self.probability = float(probability)

    def validate(self):
        if self.link in entity_correction_mapper:
            self.link = entity_correction_mapper[self.link]["entity"]
        else:
            try:
                if self.link.endswith("(disambiguation)"):
                    searchlink = self.link.replace("_(disambiguation)", "")
                    diambiguation = True
                else:
                    searchlink = self.link
                p = wikipedia.page(searchlink)
                entity_correction_mapper[self.link] = {
                    "pageid": p.pageid,
                    "entity": p.url.replace("http://en.wikipedia.org/wiki/", ""),
                    "title": p.title
                }
                self.link = entity_correction_mapper[self.link]["entity"]
                self.link = unquote(self.link)

            except DisambiguationError:
                print("Entity: ", self.link, " leads to an disambiguation error!")
            except:
                import sys

                print("Unexpected error:", sys.exc_info()[0])

    def __repr__(self):
        return "<Entity: %s %f>" % (self.link, self.probability)

