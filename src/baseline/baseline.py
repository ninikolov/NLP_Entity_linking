# -*- coding: utf-8 -*-

# baseline code

# TODO
# - Use Pickle for storing the dictionary for faster loading
# - Investigate SQL and NOSQL options (sqlite, mongodb, ...)
# - Investigate BeautifulSoup for XML processing

import csv
# import sqlite3 # not used right now
import os
from itertools import islice
from core.query import SearchQuery, SearchMatch, Entity
import sqlite3
import marshal

# This only finds out the absolute path and directory of the file
# to access the data directory
this_file = os.path.realpath(__file__)
this_dir = os.path.dirname(this_file)
rebuild_dict = False

# this could be used for a future database
DATABASE = this_dir + "../data/entitys.db"

#super_dict = {}

def load_dict(file_path):
    """
    :param file_path:
    :return:
    """
    # assert isinstance(str, file_path)
    conn = sqlite3.connect(file_path + "-db.db")
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE entity_mapping
             (words text, entities blob)''')

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
            for key in super_dict.keys():
                c.execute('insert into entity_mapping values(?, ?)', (key, marshal.dumps(super_dict[key])))

            conn.commit()
            print("Database created")

    except sqlite3.OperationalError:
        print("Database already exists, cool!")

    return conn

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
                #print(subterm)
                if subterm in new_dict.keys():
                    # print("deleting ", subterm)
                    del new_dict[subterm]
    return new_dict
import marshal

def search_entities(search_string, db_conn):
    """
    :param search_string:
    :param db_conn:
    :return:
    """
    search_query = SearchQuery(search_string)
    temp_dict = {}

    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        for query_term in window(search_query.array, n=i):
            try:
                c.execute("select * from entity_mapping where words = ?", (query_term,))
                res = c.fetchone()
                if not res:
                    continue
                # temp_result = entity_dict[query_term]
                matches = [Entity(d[0], d[1]) for d in marshal.loads(res[1])]
                temp_dict[query_term] = matches
            except KeyError:
                # print("NOT FOUND THIS KEY :(")
                pass
    temp_dict = remove_shorter_terms(temp_dict)
    for query_term, entities in temp_dict.items():
        # TODO: Fix indices to match actual location
        search_match = SearchMatch((i, i), entities, query_term)
        search_query.add_match(search_match)
    del temp_dict
    search_query.visualize()
