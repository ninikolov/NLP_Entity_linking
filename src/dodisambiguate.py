# -*- coding: utf-8 -*-

import os
import argparse
import marshal
import sys

sys.path.append("./lib/odswriter/")


from core.xml_parser import QueryParser, load_dict
from core.score import evaluate_score, print_F1
import core.query
from core.export import Export
from baseline.baseline import search_entities
from algorithms import fuzzymatch_titles
from algorithms.wikimatch import handle_queries

parser = argparse.ArgumentParser()
parser.add_argument("--testfile", "-t", help="Select XML file",
                    default="query-data-dev-set.xml")

args = parser.parse_args()

THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = args.testfile
DICT = "crosswikis-dict-preprocessed_new"
WIKI_NAMES = "enwiki-latest-all-titles-in-ns0"

ENTITY_CHECKER_MAP = "entity_map"

db_conn = load_dict(DATA_DIR + DICT)
cur = db_conn.cursor()

def update_crosswiki(entry, list_of_new_entities):
    cur.execute("select * from entity_mapping where words = ?", (entry,))
    res = cur.fetchone()
    if res:
        entities = marshal.loads(res[1])
        flat_entities = [ent[0] for ent in entities]
    else:
        entities = []
        flat_entities = entities 
    if not type(list_of_new_entities[0]) == tuple:
        add_list = [(el, 0) for el in list_of_new_entities if el not in flat_entities]
    else:
        add_list = [el for el in list_of_new_entities if el[0] not in flat_entities]

    l_add = len(add_list)
    entities = entities[:50 - l_add] + add_list + entities[50 - l_add:]
    if not res:  # No entity found for string
        #asasd
        cur.execute("insert into entity_mapping (words, entities) values (?, ?)", (entry, marshal.dumps(entities)))
    else:
        cur.execute("update entity_mapping set entities = ? where words = ?", (marshal.dumps(entities), entry))
    db_conn.commit()


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)

    # names_conn = load_wiki_names(DATA_DIR + WIKI_NAMES)
    # try:
    #     with open(DATA_DIR + ENTITY_CHECKER_MAP, "rb") as f_entity_correction_mapper: 
    #         core.query.entity_correction_mapper = marshal.load(f_entity_correction_mapper)
    # except: 
    #     print("No entity mapping cache...")

    exporter = Export()
    results = []
    for q in parser.query_array:
        # entities = search_entities(q, db_conn)
        # q.spell_check()
        # for true_match in q.true_entities:
        #     true_match.get_chosen_entity().validate()
        # fuzzymatch_titles.handle_query(q)
        print(q.array)
        r = handle_queries(q)
        for matches in r:
            if not matches[0] or not matches[1]:
                continue
            update_crosswiki(matches[0], matches[1])
        # print(r)
        results.append(r)
        # evaluate_score(q, parser)
        # q.visualize()
        # q.add_to_export(exporter)

    print("Results: \n\n", results)

    exporter.export()
    print_F1(parser)

    f_entity_correction_mapper = open(DATA_DIR + ENTITY_CHECKER_MAP, "wb+")
    marshal.dump(core.query.entity_correction_mapper, f_entity_correction_mapper)


if __name__ == "__main__":
    main()
