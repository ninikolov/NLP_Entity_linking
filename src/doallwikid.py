# -*- coding: utf-8 -*-
"""
First baseline
"""

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")

from core.xml_parser import QueryParser, load_dict
from core.score import evaluate_score, print_F1
import core.query
from core.export import Export
# from baseline.baseline import search_entities
from core.segmentation import search_entities
from algorithms.wikidata import check_wiki_data
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


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    exporter = Export()
    for query in parser.query_array:
        print(check_wiki_data(query.array))

    # exporter.export()
    # print_F1(parser)
    #
    # f_entity_correction_mapper = open(DATA_DIR + ENTITY_CHECKER_MAP, "wb+")
    # marshal.dump(core.query.entity_correction_mapper, f_entity_correction_mapper)


if __name__ == "__main__":
    main()
