# -*- coding: utf-8 -*-

import os
import argparse

import sys
sys.path.append("./lib/odswriter/")


from baseline import baseline
from core.xml_parser import QueryParser, load_dict
from core.score import evaluate_score, print_F1
parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
            default="query-data-train-set.xml")

args = parser.parse_args()
from core.export import Export

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    exporter = Export()
    for q in parser.query_array:
        entities = baseline.search_entities(q, db_conn)
        evaluate_score(q, parser)
        q.visualize()
        q.add_to_export(exporter)

    exporter.export()
    print_F1(parser)


if __name__ == "__main__":
    main()
