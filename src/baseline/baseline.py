# -*- coding: utf-8 -*-

# baseline code

# TODO
# - Use Pickle for storing the dictionary for faster loading
# - Investigate SQL and NOSQL options (sqlite, mongodb, ...)
# - Investigate BeautifulSoup for XML processing

import csv
# import sqlite3 # not used right now
import os
import pickle
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
search_string = "lance armstrong career salesman TV"


def load_dict(file_path):
    """
    Load pickled dictionary if available
    if not, build dictionary
    :param file_path: path to dict
    :return:
    """
    assert isinstance(str, file_path)
    if os.path.isfile(file_path + "-pickle"):  # if already pickled
        if rebuild_dict == False:
            pickle_file = open(file_path + "-pickle", 'rb')
            return pickle.load(pickle_file)
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
    assert isinstance(str, file_path)
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
        print("Subterms: ", subterms)
        if len(subterms) == 1:
            continue
        # Check all combinations with shorter terms
        # Remove if smaller terms already present in dictionary
        for i in range(len(subterms) - 1, 0, -1):
            for subterm in window(subterms, i):
                print(subterm)
                if subterm in dictionary.keys():
                    print("deleting ", subterm)
                    del new_dict[subterm]
    return new_dict


super_dict = load_dict(this_dir + "/../../data/crosswikis-dict-preprocessed")

search_string_arr = search_string.split()
results_dict = {}
for i in range(3, 0, -1):  # Try combinations with up to 3 words
    for query_term in window(search_string_arr, n=i):
        print("Searching for ", query_term)
        try:
            print(super_dict[query_term])
            results_dict[query_term] = super_dict[query_term]
        except KeyError:
            print("NOT FOUND THIS KEY :(")

results_dict = remove_shorter_terms(results_dict)
print(results_dict)

for key in results_dict:
    print("\n\n\nKEY: " + key + "\n==============\n")
    print(results_dict[key][0])


def old_version(search_string):
    results_dict = {}
    # create a list from the search string, splitting at spaces
    search_string_arr = search_string.split()
    # how many elements in search string
    i = len(search_string_arr)
    while i > 0:
        j = 0
        while j < i:
            # join list elements with a space
            # check out python list indexing for more information on
            # the slicing stuff: http://stackoverflow.com/questions/509211/explain-pythons-slice-notation
            temp_s = " ".join(search_string_arr[j:i])
            print(temp_s)

            try:
                # Try to find the key in the dictionary we created (superdict)
                # if key not found, then go to except
                print(super_dict[temp_s])
                results_dict[temp_s] = super_dict[temp_s]
            except:
                print("NOT FOUND THIS KEY :(")

            j += 1
        i -= 1
    return results_dict