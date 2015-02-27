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

# This only finds out the absolute path and directory of the file
# to access the data directory
this_file = os.path.realpath(__file__)
this_dir = os.path.dirname(this_file)
rebuild_dict = False

# this could be used for a future database
# DATABASE = "../data/entitys.db"

# PICKLE_FILE = "../data/pickled"

# The search string (random right now)
searchstring = "lance armstrong career"


def load_dict(file_path):
    """
    Load pickled dictionary if available
    if not, build dictionary
    :param file_path: path to dict
    :return:
    """
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


super_dict = load_dict(this_dir + "/../../data/crosswikis-dict-preprocessed")

# create a list from the search string, splitting at spaces
l = searchstring.split()

# how many elements in search string
i = len(l)
results_dict = {}
while i > 0:
    j = 0
    while j < i:
        # join list elements with a space
        # check out python list indexing for more information on
        # the slicing stuff: http://stackoverflow.com/questions/509211/explain-pythons-slice-notation
        temp_s = " ".join(l[j:i])
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

for key in results_dict:
    print("\n\n\nKEY: " + key + "\n==============\n")
    print(results_dict[key][0])