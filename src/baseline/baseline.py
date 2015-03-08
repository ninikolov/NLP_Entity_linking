# -*- coding: utf-8 -*-

# baseline code

# TODO
# - Use Pickle for storing the dictionary for faster loading
# - Investigate SQL and NOSQL options (sqlite, mongodb, ...)
# - Investigate BeautifulSoup for XML processing

import csv
# import sqlite3 # not used right now
import os
from itertools import islice
from core.query import SearchQuery, SearchMatch, Entity
import sqlite3
import marshal

# This only finds out the absolute path and directory of the file
# to access the data directory
this_file = os.path.realpath(__file__)
this_dir = os.path.dirname(this_file)
rebuild_dict = False

# this could be used for a future database
DATABASE = this_dir + "../data/entitys.db"

#super_dict = {}

def load_dict(file_path):
    """
    :param file_path:
    :return:
    """
    # assert isinstance(str, file_path)
    conn = sqlite3.connect(file_path + "-db.db")
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE entity_mapping
             (words text, entities blob)''')

        with open(file_path, "r", encoding='utf-8') as csvfile:
            # this is a csv reader
            crosswiki = csv.reader(csvfile, delimiter="\t")
            first_row = next(crosswiki)
            first_search_word = first_row[0]
            super_dict = {}
            super_dict[first_search_word] = []

            for row in crosswiki:
                # Loop through all the rows in the csv
                # row[0] contains the search string
                # if current row[0] word is different,
                # create new key in the dictionary and add a empty list
                if row[0] != first_search_word:
                    super_dict[row[0]] = []
                    first_search_word = row[0]

                # unfortunately, the csv file is not consistent
                # so the the second part (probability and entity)
                # are seperated by a space instead of a tab
                # splitting that!
                row_ = row[1].split()

                # adding the entity and prob to the list as a dictionary
                super_dict[row[0]].append((row_[1], row_[0]))

            print("Key Dict created...")
            for key in super_dict.keys():
                c.execute('insert into entity_mapping values(?, ?)', (key, marshal.dumps(super_dict[key])))

            conn.commit()
            print("Database created")

    except sqlite3.OperationalError:
        print("Database already exists, cool!")

    return conn

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

def add_new_term_check_overlap(new_match, search_query):
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
        print("         * prev:", previous_match.position, " ", 
            previous_match.substring, " (", previous_match.word_count, ")")

        if (( previous_match.position < new_match.position + new_match.word_count <
            previous_match.position + previous_match.word_count) or
            (previous_match.position < new_match.position < 
            previous_match.position + previous_match.word_count)):
            #there is an overlap
            if  (new_match.word_count < previous_match.word_count):
                #new term is shorter
                print("         *** SHORTER >> SKIP")
                return

            assert(new_match.word_count == previous_match.word_count)
            #actually wrong!!corrected afterwards
            
##            if (new_match.entity.probability < previous_match.entity.probability):
##                #new term is of same length but less probable
##                search_query.search_matches.remove(previous_match)
##                print("         *** LOWER PROB ", new_match.entity.probability, " >> SKIP")
##                return
            
            if (new_match.entity.probability < previous_match.entity.probability):
                #new term is of same length but less probable
                print("         *** LOWER PROB ", new_match.entity.probability, " >> SKIP")
                return
            else:
                #remove old match
                search_query.search_matches.remove(previous_match)
    # there is no overlap with any previous terms or new match has higher probability!
    # => Add the Entity to the search_matches array !
    search_query.add_match(new_match)
    print("    ",new_match)


def search_entities(search_query, db_conn):
    """
    :param search_string:
    :param db_conn:
    :return:
    """
    #search_query = SearchQuery(search_string)
    #print(search_query, "\n", search_query.true_entities, "\n \n" ) 
    print("\n", "="*80, "\n")
    print("####", search_query.search_string)
    
    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        pos = -1 #position of the words in the string
        print("-"*80, "\n @range ", i)
        for query_term in window(search_query.array, n=i):
            pos +=1 #windows is moved to the right
            print("    LF TERM:", query_term)
            try:
                c.execute("select * from entity_mapping where words = ?", (query_term,))
                res = c.fetchone()
                if not res:
                    print("    NOT FOUND")
                    continue
                # temp_result = entity_dict[query_term]

                entities = [Entity(d[0], d[1]) for d in marshal.loads(res[1])]
                
                #Take the highest ranked entity in the crosswiki
                new_match = SearchMatch(pos, i, entities[0], query_term)
                

                add_new_term_check_overlap(new_match, search_query)
                
                
                # for d in marshal.loads(res[1]):     
                #     print(d, "\n") 
                
                # temp_dict[query_term] = matches
            except KeyError:
                print("KEY ERROR")
                #pass


    
