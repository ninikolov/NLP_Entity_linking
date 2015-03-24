"""
TAGME
"""

import argparse
import os
import sys

import numpy as np


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from core.tagme_wrapper import *
from core.xml_parser import load_dict, QueryParser

from baseline.baseline import search_entities
from core.score import calc_tp_fp_fn

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"
# Limit how many entities we look up in the table for the voting
ENTITIES_LIMIT = 30
# Tau
PROB_LIMIT = 0.01
# parameter for pruning
THETA = 0.1


def vote(target_entity, other_entities):
    """
    Each entity from other_entities votes for target_entity. A normalized score is computed.
    :param target_entity:
    :param other_entities:
    :return:
    """
    scores = similarity_score_batch(target_entity, other_entities)
    new_length = len([x for x in scores if x and x != 0.0])
    if not scores or new_length == 0:  # if no scores were found
        return 0.
    vote_result = 0.
    for i in range(len(other_entities)):
        if scores[i] and scores[i] != 0.:  # If we found score in DB
            vote_result += other_entities[i].probability * scores[i]
    return vote_result / new_length  # normalize


def choose_entity(match1, other_matches, match_index, limit=ENTITIES_LIMIT):
    """
    Choose the entity in match1, which maximises the voting function.
    :param match1:
    :param other_matches:
    :param limit:
    :return:
    """
    match_votes = []
    for entity in match1.get_entities_limit(size_limit=limit, prob_limit=PROB_LIMIT):
        v = 0.
        for i in range(len(other_matches)):
            if match_index == i:  # looking at same match
                continue
            v += vote(entity, other_matches[i].get_entities_limit(size_limit=limit, prob_limit=PROB_LIMIT))
        match_votes.append(v)
    try:
        winner_entity = np.argmax(np.array(match_votes))
        print("Tagme chooses entity ", match1.entities[winner_entity], "for match ", match1.substring)
        match1.chosen_entity = winner_entity
    except ValueError:
        pass


def check_coherence(entity_index, other_entities, theta=THETA):
    """
    Check the coherence of an entity - how relevant it is in the context of the other selected entities.
    :param entity_index:
    :param other_entities:
    :param theta: pruning parameter
    :return:
    """
    if len(other_entities) == 1:
        return True
    other = list(other_entities)
    del other[entity_index]
    coh = vote(other_entities[entity_index], other) / (len(other_entities) - 1)
    coh += other_entities[entity_index].probability / 2
    print(coh)
    return coh > theta


def prune(query):
    """
    Remove entities that aren't coherent with the overall meaning.
    :param query:
    :return:
    """
    chosen_entities = query.get_chosen_entities()
    final_selection = []
    for index in range(len(chosen_entities)):
        if check_coherence(index, chosen_entities):
            final_selection.append(chosen_entities[index])
        else:
            query.search_matches[index].chosen_entity = -1
            print("Pruning entity ", chosen_entities[index])
    return final_selection


if __name__ == '__main__':
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    for query in parser.query_array:
        entities = search_entities(query, db_conn)
        print("Search matches: ", query.search_matches)
        for index in range(len(query.search_matches)):  # for each match
            choose_entity(query.search_matches[index], query.search_matches, index)
        final = prune(query)
        print("Final entities after pruning: ", final)
        query.visualize()


    # evaluate solution
    calc_tp_fp_fn(parser, True)