# -*- coding: utf-8 -*-

import os
import argparse

from baseline import baseline
from core.xml_parser import QueryParser, load_dict
from core.score import lazy_F1
parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
		    default="query-data-short-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)


    # for query in parser.soup.find_all("query"):
    # 	#text = query.find_all("text")[0].text
    # 	# text = query.find('annotation')
    # 	# if (text is not None):
    # 	# 	print(text.text)

    db_conn = load_dict(DATA_DIR + DICT)
    
    for q in parser.query_array:
    #for q in parser.get_all_queries_text():
        #print(q.true_entities)
        entities = baseline.search_entities(q, db_conn)

    for q in parser.query_array:
        q.visualize()
	
	#evaluate baseline solution
    lazy_F1(parser)
	

if __name__ == "__main__":
    main()
