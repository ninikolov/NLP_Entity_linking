# -*- coding: utf-8 -*-

"""
Baseline code
"""

import marshal

from core.segmentation import window, check_overlap
from core.query import Entity, SearchMatch
#from main import main


def search_entities(search_query, db_conn, take_largest=True):
    """
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
            c.execute("select * from entity_mapping where words = ?", (query_term,))
            res = c.fetchone()
            if not res:  # No entity found for string
                continue
            entities = [Entity(d[0], d[1]) for d in marshal.loads(res[1])]
            if not entities:
                continue
            # Create a match with all entities found
            new_match = SearchMatch(pos, i, entities, query_term)
            if take_largest:
                if check_overlap(new_match, search_query):
                    continue
            new_match.chosen_entity = 0
            search_query.add_match(new_match)


if __name__ == "__main__":
    main()
