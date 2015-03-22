# -*- coding: utf-8 -*-

import os
import argparse

from baseline import baseline
from core.xml_parser import QueryParser, load_dict
from core.score import F1_score
parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
		    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    
    for q in parser.query_array:
        entities = baseline.search_entities(q, db_conn)

    for q in parser.query_array:
        q.visualize()
	
	#evaluate baseline solution
    F1_score(parser)
	

if __name__ == "__main__":
    main()
