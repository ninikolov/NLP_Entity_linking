# -*- coding: utf-8 -*-

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")


from core.xml_parser import QueryParser, load_dict
from algorithms.fuzzymatch_titles import *
from algorithms.wikidata import check_wiki_data, init_wikidata

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed"
WIKI_NAMES = "enwiki-latest-all-titles-in-ns0"

ENTITY_CHECKER_MAP = "entity_map"


def do(queries):
    results = {}

    for q in queries:
        # First: Direct match:


        res = None
        if type(q) == str:
            exec_query = q
            exec_query_array = split(q)
        else:
            exec_query = q.search_string
            exec_query_array = split(q.search_string)
        print("\n\nCurrent Query: %s" % (exec_query, ))
        print(exec_query_array)

        res = check_wiki_data(exec_query_array)
        if not res:
            res = match_levenshtein(exec_query)

        if not res:
            all_direct_matches = {}
            for i in range(len(exec_query_array) + 1, 0, -1):
                for elems in window(exec_query_array, i):
                    temp_query = " ".join(elems)
                    res = match_levenshtein(temp_query)
                    print(res)

        if not res:
            res = match_all(exec_query_array)
        if not res:
            res = match_or(exec_query_array)

        if not res:
            res_query = ""
            print(exec_query)
            for query_elem, pos in tokenizer(exec_query):
                if len(query_elem) > 3 and not spell_dict.check(query_elem):
                    suggests = spell_dict.suggest(query_elem)
                    if len(suggests) == 1:
                        res_query += suggests[0]
                    else:
                        res_query += query_elem
                else:
                    res_query += query_elem
                res_query += " "
            if res_query == exec_query:
                continue
            print("Spellcheck'd: ", res_query)

            res_query_array = split(res_query)

            res = match_levenshtein(exec_query)
            print(res)
            if not res:
                print("NO RES", len(res_query_array) + 1)
                print(range(3, 0, -1))
                all_direct_matches = {}
                for i in range(len(res_query_array) + 1, 0, -1):
                    print(i)
                    for elems in window(res_query_array, i):
                        print(res, elems)

                        temp_query = " ".join(elems)
                        res = match_levenshtein(temp_query)
                        print(res)

            if not res:
                res = match_all(exec_query_array)
            if not res:
                res = match_or(exec_query_array)

        if res:
            print(exec_query, res)
            # results[q.session.session_id + ":" + q.search_string] = res
    # marshal.dump(results, open("psql_results.marshal", 'wb+'))



def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)
    db_conn = load_dict(DATA_DIR + DICT)
    init_wikidata(DATA_DIR)

    # names_conn = load_wiki_names(DATA_DIR + WIKI_NAMES)
    # try:
    #     with open(DATA_DIR + ENTITY_CHECKER_MAP, "rb") as f_entity_correction_mapper:
    #         core.query.entity_correction_mapper = marshal.load(f_entity_correction_mapper)
    # except:
    #     print("No entity mapping cache...")
    queries = []
    # queries += ['anchors resign on air', '2005 presidential election in Egypt, forgery', 'degree    hotel management?', 'web hosting services small business']
    queries += ['stagestores.com', 'bbt on line banking']

    do(parser.query_array)
    # do(queries)


if __name__ == "__main__":
    main()
