# -*- coding: utf-8 -*-

# baseline code

# TODO
# - Use Pickle for storing the dictionary for faster loading
# - Investigate SQL and NOSQL options (sqlite, mongodb, ...)
# - Investigate BeautifulSoup for XML processing

import csv
# import sqlite3 # not used right now
import os
import marshal as pickle # use marshal instead of pickle bc/ better performance
from itertools import islice

# This only finds out the absolute path and directory of the file
# to access the data directory
this_file = os.path.realpath(__file__)
this_dir = os.path.dirname(this_file)
rebuild_dict = False

# this could be used for a future database
# DATABASE = "../data/entitys.db"

# PICKLE_FILE = "../data/pickled"

# The search string (random right now)
search_string = "hanover 96 test"

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
        return "<SearchQuery: %s>" % search_string

class SearchMatch(object):
    def __init__(self, position, entities, substring):
        self.substring = substring
        self.position = position
        self.entities = entities

    def __repr__(self):
        return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, self.entities)

class Entity(object):
    def __init__(self, link, probability):
        self.link = link
        self.probability = float(probability)

    def __repr__(self):
        return "<Entity: %s %f>" % (self.link, self.probability)

super_dict = {}

def load_dict(file_path):
    """
    Load pickled dictionary if available
    if not, build dictionary
    :param file_path: path to dict
    :return:
    """
    # assert isinstance(str, file_path)
    if os.path.isfile(file_path + "-pickle"):  # if already pickled
        if rebuild_dict == False:
            pickle_file = open(file_path + "-pickle", 'rb')
            return pickle.load(pickle_file)
    global super_dict
    super_dict = build_dictionary(file_path)
    # Pickle dictionary for later use
    pickle_file = open(file_path + "-pickle", 'wb')
    pickle.dump(super_dict, pickle_file)
    return super_dict


def build_dictionary(file_path):
    """
    :param file_path:
    :return:
    """
    # assert isinstance(str, file_path)
    with open(file_path, "r", encoding='utf-8') as csvfile:
        # this is a csv reader
        crosswiki = csv.reader(csvfile, delimiter="\t")
        first_row = next(crosswiki)
        first_search_word = first_row[0]
        super_dict = {}
        super_dict[first_search_word] = []

        for row in crosswiki:
            # Loop through all the rows in the csv
            # row[0] contains the search string
            # if current row[0] word is different,
            # create new key in the dictionary and add a empty list
            if row[0] != first_search_word:
                super_dict[row[0]] = []
                first_search_word = row[0]

            # unfortunately, the csv file is not consistent
            # so the the second part (probability and entity)
            # are seperated by a space instead of a tab
            # splitting that!
            row_ = row[1].split()

            # adding the entity and prob to the list as a dictionary
            super_dict[row[0]].append((row_[1], row_[0]))

        print("Key Dict created...")
        return super_dict


def window(seq, n=3):
    """
    Returns iterator over combinations of the query terms,
    moving from left to right
    http://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python
    :param seq the target array
    :param n size of window
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield " ".join(result)
    for elem in it:
        result = result[1:] + (elem,)
        yield " ".join(result)


def remove_shorter_terms(dictionary):
    """
    Remove short terms if there are any longer terms
    :param dictionary:
    :return:
    """
    assert isinstance(dictionary, dict)
    new_dict = dict(dictionary)
    for term in dictionary.keys():
        subterms = term.split()
        # print("Subterms: ", subterms)
        if len(subterms) == 1:
            continue
        # Check all combinations with shorter terms
        # Remove if smaller terms already present in dictionary
        for i in range(len(subterms) - 1, 0, -1):
            for subterm in window(subterms, i):
                print(subterm)
                if subterm in new_dict.keys():
                    # print("deleting ", subterm)
                    del new_dict[subterm]
    return new_dict

def search_entities(search_string, entity_dict):
    search_query = SearchQuery(search_string)

    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        for query_term in window(search_query.array, n=i):
            # print("Searching for ", query_term)
            try:
                # print(super_dict[query_term])
                temp_result = entity_dict[query_term]
                matches = [Entity(d[0], d[1]) for d in temp_result]
                search_match = SearchMatch((i, i), matches, query_term)
                search_query.add_match(search_match)
            except KeyError:
                pass
                # print("NOT FOUND THIS KEY :(")

    # results_dict = remove_shorter_terms(results_dict)
    # print(results_dict)
    print(search_query.search_string + "\n==============\nEntities:\n")
    for m in search_query.search_matches:
        print(m)
        # print(m.substring + ": ")
        # print(m.entities[0])
        # print("\n")
