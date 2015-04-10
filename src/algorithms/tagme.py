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
from core.score import evaluate_score, print_F1
import math


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-short-set.xml")

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


def match_vote(target_entity, other_entities):
    """
    Each entity from other_entities votes for target_entity. A normalized score is computed.
    :param target_entity:
    :param other_entities:
    :return:
    """
    scores = similarity_score_batch(target_entity, other_entities)
    assert len(scores) == len(other_entities)
    new_length = 0
    if not scores:  # if no scores were found
        return 0., 0
    errors = 0
    vote_result = 0.
    for i in range(len(scores)):
        if scores[i] is not None:  # If we found score in DB
            vote_result += other_entities[i].probability * scores[i]
            new_length += 1
        else:
            errors += 1
    if new_length == 0:
        return 0., 0
    vote_result = vote_result / new_length  # normalize
    assert vote_result <= 1.
    return vote_result, errors


def choose_entity(target_match, matches, match_index, limit=ENTITIES_LIMIT):
    """
    Choose the entity in match1, which maximises the voting function.
    :param target_match:
    :param matches:
    :param limit:
    :return:
    """
    entity_votes = []
    other_entitites = target_match.get_entities_limit(size_limit=limit, prob_limit=PROB_LIMIT)
    total_errors = 0
    total_size = 0
    for entity in other_entitites:
        entity_vote = 0.
        for i in range(len(matches)):
            if match_index == i:  # looking at same match
                continue
            other_entitites = matches[i].get_entities_limit(size_limit=limit, prob_limit=PROB_LIMIT)
            new_vote, errors = match_vote(entity, other_entitites)
            # print("Vote ", new_vote, "for entity", entity.link, "match", matches[i].substring, " | errors:", errors)
            entity_vote += new_vote
            total_errors += errors
            total_size += len(other_entitites)
        entity_votes.append(entity_vote)
    # print("all votes: ", entity_votes)
    if not entity_votes:
        # print("Tagme didn't find anything for ", target_match.substring)
        return
    winner_entity = np.argmax(entity_votes)
    print("Tagme chooses", target_match.entities[winner_entity], "for match", target_match.substring,
          " | vote", entity_votes[winner_entity], " | errors", total_errors, " | total size", total_size,
          " | all entities", target_match.entities[0:10])
    target_match.chosen_entity = winner_entity


def check_coherence(entity_index, other_entities, theta=THETA):
    """
    Check the coherence of an entity - how relevant it is in the context of the other selected entities.
    :param entity_index:
    :param other_entities:
    :param theta: pruning parameter
    :return:
    """
    if len(other_entities) == 1:
        #print("No entities: ", other_entities)
        return True
    other = list(other_entities)
    del other[entity_index]
    vote, errors = match_vote(other_entities[entity_index], other)
    coh = vote / (len(other_entities) - 1)
    coh += other_entities[entity_index].probability / 2
    print("\t\tCoherence of ", other_entities[entity_index].link, ": ", coh)
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
            print("\t\t\tPruning entity ", chosen_entities[index])
    return final_selection


if __name__ == '__main__':
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT, fix=True)
    for query in parser.query_array:
        entities = search_entities(query, db_conn, take_largest=True)
        print("Search matches: ", query.search_matches)
        for index in range(len(query.search_matches)):  # for each match
            choose_entity(query.search_matches[index], query.search_matches, index)
        final = prune(query)
        print("Final entities after pruning: ", final)
        evaluate_score(query, parser, use_chosen_entity=True)
        query.visualize()


    # evaluate solution
    print_F1(parser)