# -*- coding: utf-8 -*-

import os
import argparse
import marshal
import sys, inspect

sys.path.append("./lib/odswriter/")
#sys.path.insert(1, '././core')
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import xml_parser

#from core.xml_parser import QueryParser, load_dict
#from ... import xml_parser
import query
from nltk.nltk_functions import chunk

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

    #exporter = Export()

    for q in parser.query_array:
        print(chunk(q.search_array))

if __name__ == "__main__":
    nltk_parser()
