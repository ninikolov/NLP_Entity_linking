# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

# XML Document documentation
# session -> mult. query

def parse_xml(file_path):
    with open(file_path) as f:
	    soup = BeautifulSoup(f)
	    return soup

def get_all_queries(soup):
	return soup.find_all("query")
