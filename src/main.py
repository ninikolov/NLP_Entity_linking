# -*- coding: utf-8 -*-

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")


from baseline import baseline
from core.xml_parser import QueryParser, load_dict, load_wiki_names
from core.score import evaluate_score, print_F1
import core.query

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
            default="query-data-short-set.xml")

args = parser.parse_args()
from core.export import Export

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
    names_conn = load_wiki_names(DATA_DIR + WIKI_NAMES)
    try:
        with open(DATA_DIR + ENTITY_CHECKER_MAP, "rb") as f_entity_correction_mapper: 
            core.query.entity_correction_mapper = marshal.load(f_entity_correction_mapper)
    except: 
        print("No entity mapping cache...")

    exporter = Export()
    for q in parser.query_array:
        entities = baseline.search_entities(q, db_conn)
        q.spell_check()
        for true_match in q.true_entities:
            true_match.get_chosen_entity().validate()
        evaluate_score(q, parser)
        q.visualize()
        q.add_to_export(exporter)

    exporter.export()
    print_F1(parser)

    f_entity_correction_mapper = open(DATA_DIR + ENTITY_CHECKER_MAP, "wb+")
    marshal.dump(core.query.entity_correction_mapper, f_entity_correction_mapper)


if __name__ == "__main__":
    main()
