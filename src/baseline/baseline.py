# -*- coding: utf-8 -*-

# baseline code

# TODO
# Use better split (Questionmark is a problem!! So seperate at all chars
# like ?!:, etc.

# import sqlite3 # not used right now
import os
from itertools import islice
import marshal
import os.path
import sys


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from core.query import Entity, SearchMatch
# This only finds out the absolute path and directory of the file
# to access the data directory
this_file = os.path.realpath(__file__)
this_dir = os.path.dirname(this_file)
rebuild_dict = False

# this could be used for a future database
DATABASE = this_dir + "../data/entitys.db"

# super_dict = {}

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


def check_overlap(new_match, search_query):
    """
    Checks if the new search term is overlapping with 
    previous search terms in the query, based on their 
    relative positions. 
    * If it is overlapping and shorter, it is not added
    (ie. the longer string is kept)
    * If it is overlapping and of same length, the entity 
    with highest probability is kept.

    :param new_match: 
    :return: Returns True if it is overlapping or 
    """

    for previous_match in search_query.search_matches:
        # print("         * prev:", previous_match.position, " ",
        # previous_match.substring, " (", previous_match.word_count, ")")

        if (( previous_match.position < new_match.position + new_match.word_count <
                      previous_match.position + previous_match.word_count) or
                (previous_match.position < new_match.position <
                         previous_match.position + previous_match.word_count)):
            # there is an overlap
            if (new_match.word_count < previous_match.word_count):
                #new term is shorter
                # print("         *** SHORTER >> SKIP")
                return True

            assert (new_match.word_count == previous_match.word_count)

            if (new_match.entities[0].probability < previous_match.entities[0].probability):
                #new term is of same length but less probable
                # print("         *** LOWER PROB ", new_match.entity.probability, " >> SKIP")
                return True
            else:
                #remove old match
                previous_match.chosen_entity = -1
    return False


def search_entities(search_query, db_conn, take_largest=True):
    """
    :param search_string:
    :param db_conn:
    :return:
    """
    # search_query = SearchQuery(search_string)
    #print(search_query, "\n", search_query.true_entities, "\n \n" ) 
    # print("entity_search", search_query.search_string)

    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        pos = -1  # position of the words in the string
        for query_term in window(search_query.array, n=i):
            pos += 1  # windows is moved to the right
            c.execute("select * from entity_mapping where words = ?", (query_term,))
            res = c.fetchone()
            if not res:  # No entity found for string
                continue
            entities = [Entity(d[0], d[1]) for d in marshal.loads(res[1])]
            # Create a match with all entities found
            new_match = SearchMatch(pos, i, entities, query_term)
            if take_largest:
                if check_overlap(new_match, search_query):
                    continue
            new_match.chosen_entity = 0
            search_query.add_match(new_match)


import itertools


def apply_f_n_combinations(text, f_n, out=[]):
    """

    :param text:
    :param f_n:
    :return:
    """
    l = text.split()
    l_size = len(l)
    if l_size == 1:
        new = f_n(text)
        if not new in out:
            return out + [new]
        return out
    for i in range(l_size, 0, -1):  # Try combinations
        to_pluralize = itertools.combinations(range(l_size), i)
        for inices in to_pluralize:
            l = text.split()
            for ind in inices:
                # print(ind)
                l[ind] = f_n(l[ind])
            final = " ".join(l)
            if not final in out:
                out.append(" ".join(l))
    return out


def get_synonym_combinations(text):
    pass


def search_entities_v2(search_query, db_conn, take_largest=True):
    """
    Just to have a second version to build upon the baseline
    :param search_string:
    :param db_conn:
    :return:
    """
    # search_query = SearchQuery(search_string)
    # print(search_query, "\n", search_query.true_entities, "\n \n" )
    # print("entity_search", search_query.search_string)

    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        pos = -1  # position of the words in the string
        for query_term in window(search_query.array, n=i):
            pos += 1  # windows is moved to the right
            options = [query_term]
            # apply_f_n_combinations(query_term, inflection.pluralize, options)
            # apply_f_n_combinations(query_term, inflection.singularize, options)
            # print("options", options)
            for option in options:
                c.execute("select * from entity_mapping where words = ?", (option,))
                res = c.fetchone()
                if not res:  # No entity found for string
                    continue
                entities = [Entity(d[0], d[1]) for d in marshal.loads(res[1])]
                # Create a match with all entities found
                new_match = SearchMatch(pos, i, entities, option)
                if take_largest:
                    if check_overlap(new_match, search_query):
                        continue
                new_match.chosen_entity = 0
                search_query.add_match(new_match)