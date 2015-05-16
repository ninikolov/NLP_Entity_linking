"""
Annotate the queries using the TAGME API.
This is the second baseline.
"""

import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from core.xml_parser import load_dict, QueryParser, QueryOutput
from core.score import evaluate_score, print_F1
from core.tagme_wrapper import tag

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-train-set.xml")

args = parser.parse_args()


THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed_new"

def run():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    # writer = QueryOutput(DATA_DIR + TRAIN_XML.replace(".", "-tagme."))
    # exporter = Export()
    for query in parser.query_array:
        tag(query)
        evaluate_score(query, parser, use_chosen_entity=True)
        query.visualize()
        # query.add_to_export(exporter)
        # writer.write_query(query)
    # exporter.export()
    # writer.commit()
    return print_F1(parser)

if __name__ == '__main__':
    run()