import argparse
import os
import sys
import pdb

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from core.tagme_wrapper import *
from core.xml_parser import load_dict, QueryParser

from core.segmentation import segmentation
from core.score import evaluate_score, print_F1
from algorithms.tagme import prune


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
ENTITIES_LIMIT = 8
# Tau
PROB_LIMIT = 0.01
# parameter for pruning
THETA = 0.1

# parameter for similarity power in dynamic programming solution
SIGMA = 1

# Parameter for session entities impact
SESSION_COEF = 2

COUNTER = 0


class Dynamic_state(object):
    def __init__(self, previous_state, value, entity, entity_index):
        self.previous_state = previous_state
        self.value = float(value)
        self.entity = entity
        self.entity_index = entity_index



def reconstruct_best_solution(state_matrix, matches):
    global COUNTER
    if len(state_matrix) >= 1:  # avoid case where matches are initially empty
        #first find best entity for last match
        max_val = 0;
        #    max_state=state_matrix[len(state_matrix)-1][0] #initialized to first one, to make nure not None!
        #    pdb.set_trace()
        #to range is exclusive!
        for index in range(len(state_matrix[len(state_matrix) - 1])):
            cur_state = state_matrix[len(state_matrix) - 1][index]
            cur_val = cur_state.value
            if max_val < cur_val:
                max_val = cur_val
                max_state = cur_state

            # if all val zero then stay none! if last iteration, set to last!
            if index == len(state_matrix[len(state_matrix) - 1]) - 1 and max_val == 0:
                max_state = cur_state
                ##print in reds
                print("{0}{1}{2}".format('\033[91m',
                                         "Max value was 0 PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP!!!",
                                         '\033[0m'))
        #set entity of last match
        current_target_match = matches[len(state_matrix) - 1]
        current_target_match.chosen_entity = max_state.entity_index
        print("Dynamic Programming chooses entity ", max_state.entity, "for match ", current_target_match.substring,
              "with value", max_val, "at index", max_state.entity_index)
        if max_state.entity_index != 0:
            COUNTER += 1

        #now reconstruct the solution following pointer from this last solution
        for index in range(2, len(state_matrix), 1):  #2 because last one already found
            max_state = max_state.previous_state
            current_target_match = matches[len(state_matrix) - index]
            current_target_match.chosen_entity = max_state.entity_index
            max_val = max_state.value
            print("Dynamic Programming chooses entity ", max_state.entity, "for match ", current_target_match.substring,
                  "with value", max_val, "at index", max_state.entity_index)
            if max_state.entity_index != 0:
                COUNTER += 1
    return


# choose entity using dynamic programming
def build_dynamic_prog_matrix(matches, state_matrix, session_entity_linked, limit=ENTITIES_LIMIT):
    """
    Choose the entity in match1, which maximises the voting function.
    :param matches:
    :param limit:
    :param state_matrix stores the state of the dynamic prog solution
    :return:
    """
    for index in range(len(matches)):  # for each match
        target_match = matches[index]
        current_states = []
        other_entitites = target_match.get_entities_limit(size_limit=limit,
                                                          prob_limit=0)  #otherwise other entities can be 0!

        #for first state
        entity_index = 0
        if index == 0:


            for entity in other_entitites:


                val = entity.probability

                # adapt entity prob depending on previous session entities using coefficients SESSION_COEF
                for j in range(len(session_entity_linked)):
                    # if already linked in session, then favor it!
                    if (session_entity_linked[j] == entity.link):
                        val *= SESSION_COEF
                        break

                new_state = Dynamic_state(None, val, entity, entity_index)
                entity_index += 1
                current_states.append(new_state)
        else:

            for entity in other_entitites:
                #keep track of max state during calculation
                max_val = 0
                max_state = None
                first_state = None

                #previous max
                previous_max_val = 0
                previous_max_state = None

                val = entity.probability

                # adapt entity prob depending on previous session entities using coefficients SESSION_COEF
                for j in range(len(session_entity_linked)):
                    # if already linked in session, then favor it!
                    if (session_entity_linked[j] == entity.link):
                        val *= SESSION_COEF
                        break

                for i in range(len(state_matrix[index - 1])):
                    similarity_val = similarity_score(entity,
                                                      state_matrix[index - 1][i].entity)  #often errors so equals zero!
                    new_val = float(state_matrix[index - 1][i].value * val * similarity_val * SIGMA)  #check float value
                    new_state = Dynamic_state(state_matrix[index - 1][i], new_val, entity, entity_index)
                    if (i == 0):
                        first_state = new_state
                        previous_max_state = Dynamic_state(state_matrix[index - 1][i], state_matrix[index - 1][i].value,
                                                           entity, entity_index)

                    #compare previous max as well
                    if state_matrix[index - 1][i].value > previous_max_val:
                        previous_max_val = state_matrix[index - 1][i].value
                        previous_max_state = Dynamic_state(state_matrix[index - 1][i], previous_max_val, entity,
                                                           entity_index)

                    if max_val < new_val:
                        max_val = new_val
                        max_state = new_state
                        ##print  OK in blue
                    #                        print("{0}{1}{2}".format('\033[94m',"OKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK!!",'\033[0m'))

                    #if last iteration and still equals null add last with low value!
                    if i == len(state_matrix[index - 1]) - 1 and max_val == 0:
                        #take previous max state as state val
                        #                        max_state=previous_max_state

                        #before first_state with artificial val
                        max_state = first_state
                        #set artificial val
                        max_val = 0.00001
                        max_state.value = max_val
                        ##print in yellow
                    #                        print("{0}{1}{2}".format('\033[93m',"Max value was 0 in state_matrix!!",'\033[0m'))
                    #                    print("For possible entity ", entity.link, " value is ", new_val)

                #set best possible state in matrix        
                current_states.append(max_state)
                entity_index += 1
                #            print("all votes: ", entity_votes)
        state_matrix.append(current_states)
    return


def get_session_info(query):
    """
    Get the following data out of the sessions: 
    - basically all entities maped so far in the session stored in session_entity_linked
    - stores also the sting difference between the last two queries in the array of strings diff_session_query 
    """
    current_session_id = query.session.session_id
    #need global keyword to modify global var
    global last_session_id
    global session_entity_linked
    global last_query_text
    global diff_session_query


    # case same session as last one
    if (last_session_id == current_session_id):
        actual_entity_linked = query.get_chosen_entities()
        for i in range(len(actual_entity_linked)):
            is_duplicate = False;
            for j in range(len(session_entity_linked)):
                #don t store duplicate
                if (actual_entity_linked[i].link == session_entity_linked[j]):
                    is_duplicate = True
                    break
            if ( not is_duplicate): session_entity_linked.append(actual_entity_linked[i].link)


        # diff between last two queries (only added ones to last query),  but beware spellings matters since simple string comparison!
        diff_session_query = []
        for i in range(len(query.array)):
            new_word = True
            for j in range(len(last_query_text)):
                if (last_query_text[j] == query.array[i]):
                    new_word = False
                    break
            if (new_word):
                diff_session_query.append(query.array[i])

        last_query_text = query.array
        return


    # case different session or first one
    else:
        last_session_id = current_session_id
        # empty list
        session_entity_linked = []
        actual_entity_linked = query.get_chosen_entities()
        for i in range(len(actual_entity_linked)):
            session_entity_linked.append(actual_entity_linked[i].link)
        # for diff
        last_query_text = query.array
        diff_session_query = []
        return

from algorithms.tagme import *
import copy

def get_confidence_score(query,total_coh):
    
    # hom many (non stop) words of initial query are matched (ratio)
    #ignore stop words?
    ratio_score=len(query.get_chosen_entities())/(len(query.array));
    
    #also use coherence score from pruning
    weight_coh=1.3
    weight_ratio=1
    confidence_score=total_coh*weight_coh+ratio_score*weight_ratio/(weight_coh+weight_ratio)
    return confidence_score

def combined():
    """
    A combination of the Dynamic Programming approach and TAGME.
    :return:
    """
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    writer = QueryOutput(DATA_DIR + TRAIN_XML.replace(".", "-tagme."))
    db_conn = load_dict(DATA_DIR + DICT, fix=False)
    exporter = Export()

    tagme_count = 0
    dyn_count = 0
    same = 0

    for query in parser.query_array:
        query_tagme = copy.deepcopy(query)
        query_dyn = copy.deepcopy(query)

        query_dyn.spell_check()
        query_tagme.spell_check()
        entities = segmentation(query_tagme, db_conn, parser, take_largest=True)
        entities = segmentation(query_dyn, db_conn, parser, take_largest=True)

        # Tagme
        for index in range(len(query_tagme.search_matches)):  # for each match
            choose_entity(query_tagme.search_matches[index], query_tagme.search_matches, index)
        for match in query_tagme.search_matches:
            try:
                match.get_chosen_entity().validate()
            except:
                continue
        for true_match in query_tagme.true_entities:
            true_match.get_chosen_entity().validate()
        final, total_coh_tagme = prune(query_tagme)

        # DP
        get_session_info(query_dyn)
        # pdb.set_trace() #for debugging

        # stores state matrix
        state_matrix = []
        build_dynamic_prog_matrix(query_dyn.search_matches, state_matrix, session_entity_linked)

        # reconstruct best solution
        reconstruct_best_solution(state_matrix, query_dyn.search_matches)
        for match in query_dyn.search_matches:
            try:
                match.get_chosen_entity().validate()
            except:
                continue
        for true_match in query_dyn.true_entities:
            true_match.get_chosen_entity().validate()
        final, total_coh_dyn = prune(query_dyn, theta=0.25)
        
        confidence_score_dyn=get_confidence_score(query_dyn,total_coh_dyn)
        print("Conficdence score for dynamic solution ",confidence_score_dyn)
        
        confidence_score_tagme=get_confidence_score(query_tagme,total_coh_tagme)
        print("Conficdence score for tagme solution ",confidence_score_tagme)
        print("Coh of Tagme:", total_coh_tagme)
        print("Coh of Dynamic:", total_coh_dyn)
        if total_coh_tagme > total_coh_dyn:
            query = query_tagme
            tagme_count += 1
        elif total_coh_tagme == total_coh_dyn:
            query = query_tagme
            same += 1
        else:
            query = query_dyn
            dyn_count += 1

        evaluate_score(query, parser, use_chosen_entity=True)
        query.visualize()
        query.add_to_export(exporter)
        writer.write_query(query)
    exporter.export()
    writer.commit()

    print("Combined solution.")
    print("Times we chose TAGME:", tagme_count, "; Dynamic:", dyn_count, "same score:", same)
    return print_F1(parser)

def dynamic():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)

    for query in parser.query_array:
        query.spell_check()
        segmentation(query, db_conn, parser, take_largest=True)
        # print("Search matches: ", query.search_matches)
        get_session_info(query)
        # pdb.set_trace() #for debugging

        # stores state matrix
        state_matrix = []
        build_dynamic_prog_matrix(query.search_matches, state_matrix, session_entity_linked)

        # reconstruct best solution
        reconstruct_best_solution(state_matrix, query.search_matches)
        # Pruning from the Tagme implementation
        final, total_coh = prune(query, theta=0.2)
        # print("Final entities after pruning: ", final)

        for match in query.search_matches:
            try:
                match.get_chosen_entity().validate()
            except:
                continue
        for true_match in query.true_entities:
            true_match.get_chosen_entity().validate()

        evaluate_score(query, parser, use_chosen_entity=True)
        print("Coherence of query:", total_coh)
        query.visualize()

    # evaluate solution
    print("Dynamic solution results:")
    print("Times we chose voted entity:", COUNTER, "out of", len(parser.query_array), "queries.")
    print_F1(parser)


if __name__ == '__main__':
    # initlialize data for session info
    last_session_id = None
    session_entity_linked = []
    last_query_text = []
    diff_session_query = []

    # dynamic()
    combined()
