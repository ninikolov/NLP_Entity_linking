# -*- coding: utf-8 -*-

"""
First baseline code & segmentation
"""

import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from core.segmentation import window, check_overlap
from core.query import Entity, SearchMatch
from core.xml_parser import QueryParser, load_dict
from core.score import evaluate_score, print_F1
from core.export import Export
import marshal

sys.path.append("./lib/odswriter/")

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"  # Original crosswiki
# DICT = "crosswikis-dict-preprocessed_new" # New Crosswiki


def segmentation_baseline(search_query, db_conn, take_largest=True):
    """
    Basic segmentation
    :param search_string:
    :param db_conn:
    :return:
    """

    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        pos = -1  # position of the words in the string
        for query_term in window(search_query.array, n=i):
            pos += 1  # windows is moved to the right
            c.execute("select * from entity_mapping where words = ?", (query_term,))
            res = c.fetchone()
            if not res:  # No entity found for string
                continue
            entities = [Entity(d[0], d[1]) for d in marshal.loads(res[1])]
            if not entities:
                continue
            # Create a match with all entities found
            new_match = SearchMatch(pos, i, entities, query_term)
            if take_largest:  # take largest match
                if check_overlap(new_match, search_query):
                    continue
            new_match.chosen_entity = 0  # choose first entity
            search_query.add_match(new_match)


def run():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    exporter = Export()
    for query in parser.query_array:
        segmentation_baseline(query, db_conn)
        evaluate_score(query, parser)
        query.visualize()
    exporter.export()
    parser.print_segmentation_stat()
    print_F1(parser)


if __name__ == '__main__':
    run()