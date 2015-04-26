"""
Functions used to perform segmentation on the queries
"""
from itertools import islice
import itertools
import marshal

from inflection import pluralize, singularize

from core.query import Entity, SearchMatch
from core.nltk.nltk_functions import hard_fix, soft_fix


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
                # new term is shorter
                # print("         *** SHORTER >> SKIP")
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
    * If it is overlapping and shorter, it is not added
    (ie. the longer string is kept)
    * If it is overlapping and of same length, the entity
    with highest probability is kept.

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


def search_entities(search_query, db_conn, take_largest=True):
    """
    New version to build upon the baseline
    :param search_string:
    :param db_conn:
    :return:
    """
    # search_query = SearchQuery(search_string)
    # print(search_query, "\n", search_query.true_entities, "\n \n" )
    # print("entity_search", search_query.search_string)

    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
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
                if take_largest:
                    if check_overlap(new_match, search_query):
                        continue
                new_match.chosen_entity = 0
                search_query.add_match(new_match)