import psycopg2
import re
import unicodedata
import marshal
import string
import enchant
from enchant.tokenize import get_tokenizer
from pprint import  pprint
import hashlib
import Levenshtein
from enum import Enum
from .wikidata import check_wiki_data
from .fuzzy_helper import *
from core.query import SearchMatch, Entity

m = hashlib.md5()

from itertools import tee

def window(iterable, size):
    iters = tee(iterable, size)
    for i in range(1, size):
        for each in iters[i:]:
            next(each, None)
    return zip(*iters)


spell_dict = enchant.Dict("en_US")
tokenizer = get_tokenizer('en_US')
conn = psycopg2.connect(database='mw', user='wolfv')




# select page.page_id, page.page_title, rd_title from page left join redirect on rd_from = page_id where page_id < 100;

def longest_common_substring(s1, s2):
   m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
   longest, x_longest = 0, 0
   for x in range(1, 1 + len(s1)):
       for y in range(1, 1 + len(s2)):
           if s1[x - 1] == s2[y - 1]:
               m[x][y] = m[x - 1][y - 1] + 1
               if m[x][y] > longest:
                   longest = m[x][y]
                   x_longest = x
           else:
               m[x][y] = 0
   return s1[x_longest - longest: x_longest]


def optimize_matches(string, matches, curr_score=0, used_elems=[]):
    pass


def check_if_abbreviation(word):
    cur = conn.cursor()

    query_string = cur.mogrify("""select page.page_id,  page.page_title, redirect.rd_title
        from page
        left outer join redirect on redirect.rd_from = page.page_id
        where page.page_title = %s
        limit 1;
    """, (word, )
    )
    el = postgres_cached(query_string, ps.FETCHONE)
    if el and el[2]:
        return el[2]
    else:
        return word



def split(string):
    return [elem[0] for elem in enchant.tokenize.basic_tokenize(string)]

def slow_insert_check(seq1, seq2):
    if len(seq1) > len(seq2):
        return 1000

    add = score = 0
    for idx, s in enumerate(seq2):
        idx_2 = idx + add
        if idx_2 >= len(seq2):
            idx_2 = len(seq2) - 1

        if seq2[idx_2] != seq1[idx]:
            score += 1
            add += 1
    return score


def deabbreviate(abbr):
    cur = conn.cursor()
    query_string = cur.mogrify("""select page.page_id,  page.page_title, redirect.rd_title
        from page
        left outer join redirect on redirect.rd_from = page.page_id
        where levenshtein_less_equal(lower(page.page_title_with_spaces), lower(%s), 1) <= 1
        order by levenshtein_less_equal(lower(page.page_title_with_spaces), lower(%s), 1);
    """, (abbr, abbr)
    )

    res = postgres_cached(query_string, ps.FETCHALL)
    ll = []
    for match in res:
        w = slow_insert_check(abbr, match[1].lower())
        ll.append({'w': w, 'm': match})

    ll.sort(key=lambda x: x['w'])
    pprint(ll[0:50])
    return "as"


    # disambiguation = wikipedia.page(abbr)
    # if disambiguation and disambiguation.content:
        # Find appropriate from disambiguation

def new_match_or(exec_query_array, evaluate):
    cur = conn.cursor()

    exec_query = " ".join(exec_query_array)
    exec_query = s = ''.join(ch for ch in exec_query if ch not in exclude)
    exec_query = " | ".join(exec_query.split())

    evaluate = ' | '.join(evaluate.split())
    # replace all special chars with nothing ascii and then remove everything else
    # exec_query = re.sub(r'[^A-Za-z0-9 ]+', '', exec_query)
    # print(exec_query)
    query_string = cur.mogrify("""select page.page_id, page.page_title, ts_rank(to_tsvector('english', page_title_with_spaces), to_tsquery(%s), 1) as rank
                   from page, to_tsquery(%s) keywords
                   where to_tsvector('english', page_title_with_spaces) @@ keywords
                   ORDER BY rank DESC""", (evaluate, exec_query, ))

    els = postgres_cached(query_string, ps.FETCHALL)
    if els:
        el, match_score = score(exec_query.split(), els)
        print(el, match_score)
        # TODO: add function to check score height
        return(get_match_or_redirect(el))


def handle_query_old(query):

    res = None

    exec_query = query.search_string
    exec_query_array = split(query.search_string)

    print("\n\nCurrent Query: %s" % (exec_query, ))
    print(exec_query_array)

    res = check_wiki_data(exec_query_array)
    if not res:
        res = match_levenshtein(exec_query)

    # if not res:
    #     all_direct_matches = {}
    #     for i in range(len(exec_query_array) + 1, 0, -1):
    #         for elems in window(exec_query_array, i):
    #             temp_query = " ".join(elems)
    #             res = match_levenshtein(temp_query)
    #             print(res)

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

        if not res_query == exec_query:
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
        entity = Entity(res, 1)
        sm = SearchMatch(0, len(query.array), [entity], query.search_string)
        query.search_matches = [sm]
        sm.chosen_entity = 0

def prune_from_search(exec_query_array, result):
    if not result:
        return []
    res_arr = result.split('_')
    res_arr = [e.lower() for e in res_arr]
    delete = []
    for q in exec_query_array:
        for r in res_arr:
            if len(longest_common_substring(q, r)) > 3 or q == r or len(q) < 2:
                delete.append(q)

    return [e for e in exec_query_array if e not in delete]

def handle_query(query):
    exec_query = query.search_string
    exec_query_array = split(query.search_string)

    print("\n\nCurrent Query: %s" % (exec_query, ))
    print(exec_query_array)

    search_array = exec_query_array
    res_list = []
    while search_array:
        res = new_match_or(search_array, query.search_string)
        if res:
            res_list.append(res)
        search_array = prune_from_search(search_array, res)
        print(search_array)
    print(res_list)


if __name__ == '__main__':
    deabbreviate('bbt')



