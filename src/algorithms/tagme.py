import os
import argparse

import numpy as np

from src.core.tagme_wrapper import *
from src.core.xml_parser import load_dict, QueryParser

from src.baseline.baseline import search_entities
from src.core.score import lazy_F1

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"


def vote(target_entity, other_entities):
    scores = similarity_score_batch(target_entity.link, [e.link for e in other_entities])
    vote_result = 0.
    for i in range(len(other_entities)):
        if scores[i] is not None:
            vote_result += other_entities[i].probability * scores[i]
    new_length = len([x for x in scores if x is not None])
    if new_length == 0:
        return 0.
    vote_result = vote_result / new_length
    # print("Vote for ", target_entity, vote_result)
    return vote_result


def votes(match1, match2):
    return [vote(entity, match2.entities) for entity in match1.get_entities()]


def all_votes(match, index, search_query):
    for i in range(len(search_query.search_matches)):
        if index == i:
            continue
        match_votes = votes(match, search_query.search_matches[i])
        winner_entity = np.argmax(np.array(match_votes))
        # print(winner_entity, search_query.search_matches[i].get_entities())
        print("Tagme chooses entity ", match.get_entities()[winner_entity], "for match ", match.substring)


if __name__ == '__main__':
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    for q in parser.query_array:
        entities = search_entities(q, db_conn)
        for i in range(len(q.search_matches)):
            all_votes(q.search_matches[i], i, q)
        q.visualize()


    # evaluate solution
    lazy_F1(parser)