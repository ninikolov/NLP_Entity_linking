# -*- coding: utf-8 -*-

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")

from src.baseline import baseline
from core.xml_parser import QueryParser, load_dict
from core.score import evaluate_score, print_F1
import core.query
from core.export import Export
from core.nltk.nltk_functions import chunk

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


def nltk_parser():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)

    # names_conn = load_wiki_names(DATA_DIR + WIKI_NAMES)
    # try:
    #     with open(DATA_DIR + ENTITY_CHECKER_MAP, "rb") as f_entity_correction_mapper: 
    #         core.query.entity_correction_mapper = marshal.load(f_entity_correction_mapper)
    # except: 
    #     print("No entity mapping cache...")

    exporter = Export()

    for q in parser.query_array:
        print(chunk(q.search_array))

if __name__ == "__main__":
    nltk_parser()
