# -*- coding: utf-8 -*-

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")


from core.xml_parser import QueryParser, load_dict
from algorithms import fuzzymatch_titles
parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"
WIKI_NAMES = "enwiki-latest-all-titles-in-ns0"

ENTITY_CHECKER_MAP = "entity_map"
queries = ['anchors resign on air', '2005 presidential election in Egypt, forgery', 'degree    hotel management?', 'web hosting services small business']


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)

    # names_conn = load_wiki_names(DATA_DIR + WIKI_NAMES)
    # try:
    #     with open(DATA_DIR + ENTITY_CHECKER_MAP, "rb") as f_entity_correction_mapper:
    #         core.query.entity_correction_mapper = marshal.load(f_entity_correction_mapper)
    # except:
    #     print("No entity mapping cache...")


    fuzzymatch_titles.do(parser.query_array)
    # fuzzymatch_titles.do(queries)


if __name__ == "__main__":
    main()
