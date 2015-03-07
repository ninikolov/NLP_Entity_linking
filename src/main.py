# -*- coding: utf-8 -*-

import os

from src.baseline import baseline
from src.core.xml_parser import QueryParser


THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/data/"
TRAIN_XML = "query-data-dev-set.xml"
DICT = "crosswikis-dict-preprocessed"


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    entity_dict = baseline.load_dict(DATA_DIR + DICT)
    for q in parser.get_all_queries_text():
        entities = baseline.search_entities(q, entity_dict)


if __name__ == "__main__":
    main()
