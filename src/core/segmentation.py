"""
Functions used to perform segmentation on the queries
"""
from itertools import islice
import marshal

from inflection import pluralize, singularize
from collections import defaultdict
from operator import itemgetter

from core.helper import TermColor, color_print
from core.query import Entity, SearchMatch
from core.nltk.nltk_functions import hard_fix, soft_fix, chunk, get_array

import nltk

def window(seq, n=3):
    """
    Returns iterator over combinations of the query terms,
    moving from left to right
    http://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator-in-python
    :param seq the target array
    :param n size of window
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield " ".join(result)
    for elem in it:
        result = result[1:] + (elem,)
        yield " ".join(result)


def check_overlap(new_match, search_query):
    """
    Checks if the new search term is overlapping with
    previous search terms in the query, based on their
    relative positions.
    * If it is overlapping and shorter, it is not added
    (ie. the longer string is kept)
    * If it is overlapping and of same length, the entity
    with highest probability is kept.

    :param new_match:
    :return: Returns True if it is overlapping or
    """

    for previous_match in search_query.search_matches:
        if not previous_match.entities:
            continue
        # print("         * prev:", previous_match.position, " ",
        # previous_match.substring, " (", previous_match.word_count, ")")

        if (( previous_match.position < new_match.position + new_match.word_count <
                      previous_match.position + previous_match.word_count) or
                (previous_match.position < new_match.position <
                         previous_match.position + previous_match.word_count)):
            # there is an overlap
            if (new_match.word_count < previous_match.word_count):
                # new term is shorter)
                return True

            assert (new_match.word_count == previous_match.word_count)

            if (new_match.entities[0].probability < previous_match.entities[0].probability):
                # new term is of same length but less probable
                # print("         *** LOWER PROB ", new_match.entity.probability, " >> SKIP")
                return True
            else:
                # remove old match
                previous_match.chosen_entity = -1
    return False


def check_overlap_v2(match2, search_query):
    """
    Checks if the new search term is overlapping with
    previous search terms in the query, based on their
    relative positions.
    * If it is overlapping, the one with the less entities 
    is kept
    :param match2:
    :return: Returns True if it is overlapping or
    """

    for match1 in search_query.search_matches:
        if not match1.entities:
            continue
        for match2 in search_query.search_matches:

            # print("         * prev:", previous_match.position, " ",
            # previous_match.substring, " (", previous_match.word_count, ")")

            if (( match1.position < match2.position + match2.word_count <
                          match1.position + match1.word_count) or
                    (match1.position < match2.position <
                             match1.position + match1.word_count)):
                # there is an overlap
                # if (new_match.word_count < previous_match.word_count):
                # #new term is shorter
                # # print("         *** SHORTER >> SKIP")
                # return True
                #
                # assert (new_match.word_count == previous_match.word_count)

                if (len(match2.entities) < len(match1.entities)):
                    # new term is of same length but less probable
                    # print("         *** LOWER PROB ", new_match.entity.probability, " >> SKIP")
                    return True
                else:
                    # remove old match
                    match1.chosen_entity = -1

    return False


def check_overlap_simple(new_match, search_query):
    """
    Checks if the new search term is overlapping with
    previous search terms in the query, based on their
    relative positions.

    :param new_match:
    :return: Returns the overlapping Term or False
    """

    for match1 in search_query.search_matches:
        if ((not match1.entities) or match1.entities == -1):
            continue
    
        if (( match1.position < new_match.position + new_match.word_count <
                      match1.position + match1.word_count) or
                (match1.position < new_match.position <
                         match1.position + match1.word_count)):
            # there is an overlap
            return match1
    return False


def apply_f_n_combinations(text, f_n, out=[]):
    """
    Generate combinations of words by applying function
    :param text: the string of text
    :param f_n: the function
    :return: array of combinations
    """
    l = text.split()
    l_size = len(l)
    if l_size == 1:
        new = f_n(text)
        if not new in out:
            return out + [new]
        return out
    for i in range(l_size, 0, -1):  # Try combinations
        to_pluralize = itertools.combinations(range(l_size), i)
        for inices in to_pluralize:
            l = text.split()
            for ind in inices:
                # print(ind)
                l[ind] = f_n(l[ind])
            final = " ".join(l)
            if not final in out:
                out.append(" ".join(l))
    return out


def get_synonym_combinations(text):
    pass


def get_entities(cursor, target):
    cursor.execute("select * from entity_mapping where words = ?", (target,))
    return cursor.fetchone()


import itertools
from copy import deepcopy

def slice_by_lengths(lengths, the_list):
    for length in lengths:
        new = []
        for i in range(length):
            new.append(the_list.pop(0))
        yield new

def subgrups(my_list):
    for each_tuple in partition(len(my_list)):
        yield list(slice_by_lengths(each_tuple, deepcopy(my_list)))

def partition(number):
    return {(x,) + y for x in range(1, number) for y in partition(number - x)} | {(number,)}

def word_combinations(query):
    combinations = []
    words = query.split()
    for group in subgrups(words):
        combinations.append([" ".join(group[i]) for i in range(len(group))])
    return combinations

def segmentation(search_query, db_conn, parser, take_largest=True):
    """
    New version to build upon the baseline
    :param search_string:
    :param db_conn:
    :return:
    """
    # search_query = SearchQuery(search_string)
    # print(search_query, "\n", search_query.true_entities, "\n \n" )
    # print("entity_search", search_query.search_string)

    del_index = [] #array of positions of deleted stopwords

    last_session_id = None
    session_entity_linked = []
    last_query_text = []
    diff_session_query = []
    #get_session_info(search_query)

    c = db_conn.cursor()
    search_query.array, del_index = delete_stop_words(search_query.array)
    for i in range(len(search_query.array), 0, -1):  # Try combinations with up to n words
        pos = -1  # position of the words in the string
        for query_term in window(search_query.array, n=i):
            pos += 1  # windows is moved to the right
            options = [query_term]
            # apply_f_n_combinations(query_term, inflection.pluralize, options)
            # apply_f_n_combinations(query_term, inflection.singularize, options)
            # print("options", options)
            for option in options:
                # methods to apply to try to find something that works
                # TODO: Figure out smarter ways to use these
                operations = [singularize, pluralize, soft_fix, hard_fix]
                result = get_entities(c, option)
                while not result and operations:  # apply operations in order until there's results
                    fixed = operations[0](option)
                    result = get_entities(c, fixed)
                    if operations[0] == hard_fix and result and fixed != option:
                        print("Fixed", option, "to", fixed)
                    del operations[0]
                if not result and not operations:
                    continue
                entities = [Entity(d[0], d[1]) for d in marshal.loads(result[1])]
                if not entities:
                    continue
                # Create a match with all entities found
                new_match = SearchMatch(pos, i, entities, option)
                overlap = check_overlap_simple(new_match, search_query)
                if overlap:
                    # print("****-----****-----****-----****-----")
                    s1 = segment_score(new_match, parser) 
                    s2 = segment_score(overlap, parser)

                    # print("OVERLAP ", s1,
                    #      " vs ",s2)

                    #check if score of new segment is higher
                    if s1 < s2:
                        #NO, it isn't ! so ignore 
                        continue
                    #remove old match
                    search_query.search_matches.remove(overlap)

                # overlap = check_overlap(new_match, search_query)
                # if overlap: 
                #     continue
                    
                new_match.chosen_entity = 0
                search_query.add_match(new_match)

    # #readjust the entitie's position
    # for match in search_query.search_matches:
    #     for del_ind in del_index:
    #         if (del_ind <= match.position):
    #             match.position += 1
                

def delete_stop_words(array):
    stop_words = set(('and', 'or', 'not', 'for', 'in', 'why', 'is', 'how', 
        'do', 'has', 'to'))
    del_index = []
    for word in array:
        if word in stop_words:
            del_index.append(array.index(word))
            array.remove(word)

    return array, del_index

    # new = [word for word in array if word not in stop_words]
    # return new

def segmenter(array):

    #tokenized = nltk.word_tokenize(text)
    tagged = nltk.pos_tag(array)
    s = chunk(tagged)
    print("-------")
    print(tagged)

    for c in s:
        for word in c:
            print (word)

def count_prepositions(array):
    tagged = nltk.pos_tag(array)

def segment_score(search_match, parser):

    score = [0,0,0,0]
    #WEIGHT OF SEGMENTATION SCORES ARE DEFINED HERE **
    #First weight : Word count (normalized)
    #Second weight : Amount of entities (normalized)
    #Third weight : Lexial Homogeneity 
    #Fourth weight : Highest Entity Probability 

    #weights = [100/parser.avg_word, 1/parser.avg_entities, 1, 1]
    #weights = [1/1.5, 380, 3, 1]
    #weights = [1/parser.avg_word, 0, 1.5, 3]
    weights = [3, 3, 1, 3]

    score[0] = search_match.word_count
    score[1] = 1/len(search_match.entities)
    score[2] = homogeneity(search_match.substring)
    score[3] = search_match.entities[0].probability
    parser.word_count_all.append(score[0])
    parser.entity_count_all.append(score[1])

    # color_print(search_match.substring, TermColor.GREEN)
    # color_print("word count score: "+ str(score[0]) + 
    #     " (avg " + str(parser.avg_word) + ")")
    # color_print("entities count score: "+ str(score[1])+ 
    #     " (avg " + str(parser.avg_entities) + ")")
    # color_print("homogeneity score: "+ str(score[2]))
    # color_print("probability score: "+ str(score[3]))
    return sum([a*b for a,b in zip(weights,score)])

def homogeneity(string):

    """
    Returns a score based on how many different 
    types of words are in the string (ADJ, NOUN, etc)
    One type returns a score s=1, 2 types s=0.5, 3 types s=0.
    """
    array = nltk.word_tokenize(string)
    tagged = nltk.pos_tag(array)

    counts = defaultdict(int)
    for (word, tag) in tagged:
        counts[tag] += 1
    #print(tagged)
    #print(sorted(counts.items(), key=itemgetter(1), reverse=True))
    return(max(1.5-len(counts.items())/2, 0))


# def get_session_info(query):
#     """
#     Get the following data out of the sessions: 
#     - basically all entities maped so far in the session stored in session_entity_linked
#     - stores also the sting difference between the last two queries in the array of strings diff_session_query 
#     """
#     current_session_id = query.session.session_id
#     #need global keyword to modify global var
#     global last_session_id
#     global session_entity_linked
#     global last_query_text
#     global diff_session_query


#     # case same session as last one
#     if (last_session_id == current_session_id):
#         actual_entity_linked = query.get_chosen_entities()
#         for i in range(len(actual_entity_linked)):
#             is_duplicate = False;
#             for j in range(len(session_entity_linked)):
#                 #don t store duplicate
#                 if (actual_entity_linked[i].link == session_entity_linked[j]):
#                     is_duplicate = True
#                     break
#             if ( not is_duplicate): session_entity_linked.append(actual_entity_linked[i].link)


#         # diff between last two queries (only added ones to last query),  but beware spellings matters since simple string comparison!
#         diff_session_query = []
#         for i in range(len(query.array)):
#             new_word = True
#             for j in range(len(last_query_text)):
#                 if (last_query_text[j] == query.array[i]):
#                     new_word = False
#                     break
#             if (new_word):
#                 diff_session_query.append(query.array[i])

#         last_query_text = query.array
#         return


#     # case different session or first one
#     else:
#         last_session_id = current_session_id
#         # empty list
#         session_entity_linked = []
#         actual_entity_linked = query.get_chosen_entities()
#         for i in range(len(actual_entity_linked)):
#             session_entity_linked.append(actual_entity_linked[i].link)
#         # for diff
#         last_query_text = query.array
#         diff_session_query = []
#         return


