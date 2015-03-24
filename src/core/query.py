# -*- coding: utf-8 -*-
class TermColor:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

import re
class SearchQuery(object):
    def __init__(self, search_string):
        self.search_string = search_string
        self.array = re.findall(r"[\w]+", search_string)
        self.search_matches = []
        self.true_entities = []

    def add_match(self, match):
        # match: SearchMatch
        self.search_matches.append(match)

    def rank_matches(self):
        pass

    def __repr__(self):
        #return "<SearchQuery: %s>" % self.search_string
        return self.search_string

    def get_chosen_entities(self):
        return [m.entities[m.chosen_entity] for m in self.search_matches if m.chosen_entity >= 0]

    def clean(self):
        for match in self.search_matches:
            match.clean()


    # def choose_best_entities(self):
    #     """
    #     TODO: Figure out a better way to do this
    #     """
    #     best_entities = {}
    #     for match in self.search_matches:
    #         substring, entity = match.choose_best_match()
    #         best_entities[substring] = entity
    #     return best_entities

    def get_search_string(self):
        return self.search_string

    def visualize(self):

        colors = {'TP-strict': TermColor.GREEN, 'TP-lazy': TermColor.YELLOW, 
            'FP': TermColor.RED,'FN': TermColor.RED, "": TermColor.CYAN}

        #The query is normally visualised once. But if some matches are overlapping, we will need to show
        #the string more than once so that all the matches can be seen.
        visu = [] #search string visalization
        index_ssv = 0 #index search string vizualization
        
        search_matches_copy = list(self.search_matches) 

        while len(search_matches_copy)>0:
            word_pointer = 0
            visu.append("")
            while word_pointer < len(self.array):
                #in this loop we go through the words in the query array and look if there are corresponding matches
                match_exists = False
                for match in search_matches_copy:
                    if (not match.rating):
                        search_matches_copy.remove(match)
                        break #This should normally not happen. However it seems that it happens in the case where
                        #the xml is incomplete (check dev-set "New York American Girl dolls cost"). TODO : Look into that.
                    if match.position == word_pointer:
                        #we check the starting position of the match.
                        #followed by an assert : check if the words (not ony position) coincide 
                        assert(match.substring.split()[0] == self.array[word_pointer])
                        visu[index_ssv] +=  "{0}{1}{2} ".format(
                            colors[match.rating], match.substring, TermColor.END)
                        word_pointer += match.word_count
                        if (word_pointer < len(self.array)):
                            visu[index_ssv] += "| " #Separate the matches
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
        print (" |&| ".join(visu))
        for match in self.search_matches:
            print("{0}{1:<25} | {2}{3}".format(colors[match.rating],
                match.substring, match.entities[0], TermColor.END))
        
        first=True
        for true_match in self.true_entities:
            if (true_match.rating == "FN"):
                if (first):
                    print("Fale negatives (missed entities):")
                first = False
                print("{0}{1:<25} | {2}{3}".format(colors[true_match.rating],
                    true_match.substring, true_match.entities[0], TermColor.END))
        print("-"*80 + "\n")

class SearchMatch(object):
    def __init__(self, position, word_count, entities, substring):
        self.substring = substring
        self.position = position
        self.word_count = word_count
        self.entities = entities
        self.chosen_entity = -1 # a positive number indicates array index 
                                # of chosen entity, -1 == no entity chosen
        self.rating = "" # "TP-strict", "TP-lazy", "FP", "FN"

    def __repr__(self):
        return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, self.entities[0])

    def get_chosen_entity(self):
        if self.chosen_entity >= 0:
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
    #     """
    #     """
    #     return self.substring, self.entities[0]

class Entity(object):
    def __init__(self, link, probability):
        self.link = link
        self.probability = float(probability)

    def __repr__(self):
        return "<Entity: %s %f>" % (self.link, self.probability)
