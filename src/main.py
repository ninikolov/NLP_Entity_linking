# -*- coding: utf-8 -*-

from core import xml_parser, score
from baseline import baseline

import os

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = "query-data-dev-set.xml"
DICT = "crosswikis-dict-preprocessed"

def main():
    entity_dict = baseline.load_dict(DATA_DIR + DICT)
    xml = xml_parser.parse_xml(DATA_DIR + TRAIN_XML)
    for q in xml_parser.get_all_queries(xml):
        for t in q.find_all("text"):
            entities = baseline.search_entities(t.text, entity_dict)


if __name__ == "__main__":
    main()
