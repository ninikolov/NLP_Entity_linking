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
#from baseline.baseline import search_entities
from core.segmentation import search_entities

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-short-set.xml")

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
        entities = search_entities(query, db_conn)
        # query.spell_check()
        # for true_match in query.true_entities:
        #     true_match.get_chosen_entity().validate()
        evaluate_score(query, parser)
        query.visualize()
        print("ADDING TO EXORT")
        query.add_to_export(exporter)

    exporter.export()
    print_F1(parser)

    f_entity_correction_mapper = open(DATA_DIR + ENTITY_CHECKER_MAP, "wb+")
    marshal.dump(core.query.entity_correction_mapper, f_entity_correction_mapper)


if __name__ == "__main__":
    main()
