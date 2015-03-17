# -*- coding: utf-8 -*-

import sqlite3
import marshal
import csv
import re

from bs4 import BeautifulSoup

from .query import SearchQuery, SearchMatch, Entity

# XML Document documentation
# session -> mult. query

def parse_xml(file_path):
    with open(file_path) as f:
        soup = BeautifulSoup(f, ["lxml", "xml"])
        assert isinstance(soup, BeautifulSoup)
        return soup

class QueryParser():
    """
    A QueryParser stores and manages our queries.
    """
    def __init__(self, file_path):
        """
        :param file_path: path to xml file to be used
        """
        self.soup = parse_xml(file_path)
        self.query_array = []
        self._build_queries()

    def get_all_queries_text(self):
        """
        :return: An array with the text of the queries
        """
        return [a.__repr__() for a in self.query_array]

    def _build_queries(self):
        """Populate our array of SearchQuery items.
        TODO: Add actual position and length of query of term in query
        Both Currently 0 by default
        """
        self.query_array = []
        for query in self.soup.find_all("query"):
            text = query.find_all("text")[0].text
            new_query = SearchQuery(text)
            for ann in query.find_all("annotation"):
                try:
                    e = Entity(ann.find_all("target")[0].text, 0)
                except IndexError: # No true_entitiesntity here
                    e = Entity("None", 0)
                try:
                    span = ann.find_all("span")[0].text
                    # find the amount of word separators in the string before the occurence of span
                    str_before = re.match(r"\W*(.*)%s" % span, new_query.search_string, re.IGNORECASE)
                    pos = len(re.findall(r"[\W]+", str_before.group(1), re.IGNORECASE))
                    assert(isinstance(pos, int))

                    new_query.true_entities.append(SearchMatch(pos, len(span.split()), [e], span))
                except:
                    print("Couldn't add \"%s\", there was some issue" % text)
                    new_query = None
                #print("LINK: " + e.link)
            if new_query:
                self.query_array.append(new_query)


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
             (words TEXT, entities BLOB)''')

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
                c.execute('INSERT INTO entity_mapping VALUES(?, ?)', (key, marshal.dumps(super_dict[key])))

            conn.commit()
            print("Database created")

    except sqlite3.OperationalError:
        print("Database already exists, cool!")

    return conn

