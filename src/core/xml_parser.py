# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from core.query import SearchQuery, SearchMatch, Entity

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
        self.__build_queries()

    def get_all_queries_text(self):
        """
        :return: An array with the text of the queries
        """
        return [a.__repr__() for a in self.query_array]

    def __build_queries(self):
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
                new_query.true_entities.append(SearchMatch(0, 0, [e], ann.find_all("span")[0].text)) #TODO:set correct positions
                #print("LINK: " + e.link)
            self.query_array.append(new_query)

