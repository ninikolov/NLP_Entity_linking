"""
TAGME
"""

import argparse
import os
import sys


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from core.tagme_wrapper import *
from core.xml_parser import load_dict, QueryParser

from core.segmentation import search_entities
from core.score import evaluate_score, print_F1
import math
from core.export import Export
import numpy as np


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()


THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed_new"
# Limit how many entities we look up in the table for the voting
ENTITIES_LIMIT = 50
# Tau
PROB_LIMIT = 0.005
# parameter for pruning
THETA = 0.3
# Minimal acceptable vote for an entity to select it
# If nobody has vote above this we'll just take the top entity
EPSILON = 0.1
#
DEBUG = True


def rel(target_entity, other_entities):
    scores = similarity_score_batch(target_entity, other_entities, ignore_missing=True)
    assert len(scores) == len(other_entities)
    return np.sum(scores)


def match_vote(target_entity, other_entities, normalize=True):
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
    if normalize:
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
            match_entitites = matches[i].get_entities_limit(size_limit=limit, prob_limit=PROB_LIMIT)
            new_vote, errors = match_vote(entity, match_entitites)
            entity_vote += new_vote
            total_errors += errors
            total_size += len(match_entitites)
        entity_votes.append(entity_vote)
    if not entity_votes:
        # print("Tagme didn't find anything for ", target_match.substring)
        return
    # winner_entity = np.argmax(entity_votes)
    winner_entity = choose_best_epsilon(other_entitites, entity_votes)
    if DEBUG:
        print("Tagme chooses", target_match.entities[winner_entity], "for match", target_match.substring,
              " | vote", entity_votes[winner_entity], " | errors", total_errors, " | total size", total_size)
        print([(other_entitites[i].link, "V=" + str(entity_votes[i])) for i in range(len(other_entitites[0:10]))])
    target_match.chosen_entity = winner_entity


def choose_best_epsilon(entities, votes, epsilon=EPSILON):
    top = 0.
    top_ind = -1
    for i in range(len(votes)):
        if votes[i] < epsilon:
            continue
        if entities[i].probability > top:
            top = entities[i].probability
            top_ind = i
    if top_ind < 0:
        # print("Opting for default entity")
        return 0
    return top_ind


def choose_best_size_limit(entities, votes, part_limit=10):
    if len(votes) <= part_limit:
        ind = range(len(votes))
    else:
        ind = np.argpartition(np.array(votes), -part_limit)[-part_limit:]
    top = 0.
    top_ind = -1
    for i in ind:
        if entities[i].probability > top:
            top = entities[i].probability
            top_ind = i
    return top_ind

def check_coherence(entity_index, other_entities, theta=THETA):
    """
    Check the coherence of an entity - how relevant it is in the context of the other selected entities.
    :param entity_index:
    :param other_entities:
    :param theta: pruning parameter
    :return:
    """
    if len(other_entities) == 1:
        # print("No entities: ", other_entities)
        return True
    other = list(other_entities)
    del other[entity_index]
    vote = rel(other_entities[entity_index], other)
    coh = vote / (len(other_entities) - 1)
    coh += other_entities[entity_index].probability / 2
    if DEBUG:
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
            if DEBUG:
                print("\t\t\tPruning entity ", chosen_entities[index])
    return final_selection


def run():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT, fix=False)
    exporter = Export()
    for query in parser.query_array:
        query.spell_check()
        entities = search_entities(query, db_conn, take_largest=True)
        if DEBUG:
            print("Search matches: ", query.search_matches)
        for index in range(len(query.search_matches)):  # for each match
            choose_entity(query.search_matches[index], query.search_matches, index)
        final = prune(query)
        if DEBUG:
            print("Final entities after pruning: ", final)
        for true_match in query.true_entities:
            true_match.get_chosen_entity().validate()
        evaluate_score(query, parser, use_chosen_entity=True)
        query.visualize()
        query.add_to_export(exporter)
    exporter.export()

    # evaluate solution
    print("Tagme results with parameters ENTITIES_LIMIT=", ENTITIES_LIMIT, "PROB_LIMIT=", PROB_LIMIT, "THETA=", THETA,
          "EPSILON=", EPSILON, ".")
    return print_F1(parser)


if __name__ == '__main__':
    # f1s = {}
    # for e in [0.01, 0.005, 0.001]:
    # PROB_LIMIT = e
    # f1s[e] = run()
    # print(f1s)
    run()

