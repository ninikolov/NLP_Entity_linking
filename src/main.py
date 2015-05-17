# -*- coding: utf-8 -*-
"""
File for playing with things
First baseline is in baseline.baseline.py
Other approaches are in the algorithms package
"""

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")


from core.xml_parser import QueryParser, load_dict
from core.score import evaluate_score, print_F1
import core.query 
from core.query import Session_info
from core.export import Export
#from baseline.baseline import search_entities
from core.segmentation import segmentation
from algorithms.tagme import prune

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed_new"
WIKI_NAMES = "enwiki-latest-all-e-in-ns0"

ENTITY_CHECKER_MAP = "entity_map"


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    exporter = Export()
    
    session_info_ob=Session_info()
    
    for query in parser.query_array:
        segmentation(query, db_conn, parser,session_info_ob)
        query.spell_check()
        for true_match in query.true_entities:
            true_match.get_chosen_entity().validate()
        #entities = search_entities(query, db_conn)
        evaluate_score(query, parser)
        query.visualize()
        #print("ADDING TO EXORT")
        query.add_to_export(exporter)
        #parser.update_segmentation_averages()

    exporter.export()
    parser.print_segmentation_stat()
    print_F1(parser)

    f_entity_correction_mapper = open(DATA_DIR + ENTITY_CHECKER_MAP, "wb+")
    marshal.dump(core.query.entity_correction_mapper, f_entity_correction_mapper)


if __name__ == "__main__":
    main()
