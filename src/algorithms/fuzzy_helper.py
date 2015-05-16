import psycopg2
import re
import unicodedata
import marshal
import string
import enchant
from enchant.tokenize import get_tokenizer
from pprint import  pprint
import hashlib
from enum import Enum
import redis


from core.query import SearchMatch, Entity
spell_dict = enchant.Dict("en_US")
tokenizer = get_tokenizer('en_US')
conn = psycopg2.connect(database='mw', user='wolfv')

r_cache = redis.StrictRedis(host='localhost', port=6379, db=0)


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return only_ascii
exclude = set(string.punctuation)


class ps(Enum):
    FETCHONE = 1
    FETCHALL = 2

def get_score(substr1, match_elems):
    # print(substr1)
    for m in match_elems:
        if m == substr1:
            return len(substr1) + 1 # better if complete match!
        elif m.startswith(substr1):
            return len(substr1)
        elif substr1 in m and len(substr1) >= 3:
            return len(substr1) - 2 # Add something if at least in the word
    return -1



def score(elems, matches):
    prev_match_score = prev_match_length = 0
    chosen = ''
    elems = [elem for elem in elems if elem != '|']
    elem_string = " ".join(elems)
    # print(elem_string)
    match_elems = [match[1].replace('_', ' ').lower().split() for match in matches]
    potential_max_score = len(elem_string)
    # print(match_elems)
    chosen_idx = 0
    max_psql_score = matches[0][2] # sorted by score
    for idx, match in enumerate(match_elems):
        curr_match = matches[idx]
        curr_match_psql_score = curr_match[2]
        curr_match_string = matches[idx][1]
        match_score = 0
        if curr_match_psql_score < 0.9 * max_psql_score:
            break
        prev_match_idx = -2
        for elem_idx, elem in enumerate(elems):

            while len(elem):
                temp_score = get_score(elem.lower(), match)
                # print(temp_score, match)

                if temp_score > 0:
                    streak = 1 if prev_match_idx == elem_idx - 1 else 0
                    prev_match_idx = elem_idx
                    # if streak:
                    #     print("STREACK")
                    match_score += temp_score + streak + 1 # add plus one for amount of matched substrings

                    # TODO maybe remove substring from query ...
                    break
                else:
                    elem = elem[:-1]
        # if len(curr_match_string) > len(elem_string):
        #     match_score /= (abs(potential_max_score - (len(curr_match_string))) / potential_max_score)
        # match_score = curr_match[2]
        if match_score > prev_match_score or (prev_match_length > len(curr_match_string) and match_score == prev_match_score):
            prev_match_length = len(curr_match_string)
            if len(curr_match_string) > len(elem_string) + 8:
                # dont add
                pass
            else:
                # print(match_score, matches[idx])
                # pprint(match_elems[idx])
                # pprint(elems)
                chosen = matches[idx]
                chosen_idx = idx
                prev_match_score = match_score
    # print(matches)
    # if not chosen_idx:
    #     return None
    # print(matches)
    return (matches[chosen_idx], match_score)


def postgres_cached(query, multi):
    key = (hashlib.md5(bytes(query) + str(multi).encode('utf-8'))).hexdigest()
    if r_cache.get(key):
        res = marshal.loads(r_cache.get(key))
        # print("WEVE GOT A CACHE HIT: ", res)
        return res
    else:
        cur = conn.cursor()
        cur.execute(query)
        if multi == ps.FETCHONE:
            res = cur.fetchone()
        else:
            res = cur.fetchall()
        mdump = marshal.dumps(res)
        r_cache.set(key, mdump)
        return res


def get_match_or_redirect(el):
    cur2 = conn.cursor()

    if type(el) == list or type(el) == tuple:
        # print("GETTING A MATCH .. .", el)
        res = el[1]
        cur2.execute("""select redirect.rd_title from redirect where rd_from = %s""", (el[0], ))
        rd = cur2.fetchone()
        if rd:
            return rd[0].replace("''", "'")
        else:
            return el[1].replace("''", "'") # table contains these weird double quotes
    elif type(el) == str:
        cur2.execute("""select redirect.rd_title from redirect where rd_from = %s""", (el, ))
        rd = cur2.fetchone()
        # print(rd)
        if rd:
            return rd[0].replace("''", "'")
        else:
            return el.replace("''", "'") # table contains these weird double quotes

    else:
        return None


def match_levenshtein(exec_query):

    cur = conn.cursor()
    query_string_fast = cur.mogrify("""select page.page_id,  page.page_title, redirect.rd_title
        from page
        left outer join redirect on redirect.rd_from = page.page_id
        where lower(%s) = lower(page.page_title_with_spaces)
    """, (exec_query, )
    )
    el = postgres_cached(query_string_fast, ps.FETCHONE)
    if el:
        return get_match_or_redirect(el)
    query_string = cur.mogrify("""select page.page_id,  page.page_title, redirect.rd_title
        from page
        left outer join redirect on redirect.rd_from = page.page_id
        where levenshtein_less_equal(lower(page.page_title_with_spaces), lower(%s), 2) <= 2
        order by levenshtein_less_equal(lower(page.page_title_with_spaces), lower(%s), 2);
    """, (exec_query, exec_query)
    )

    el = postgres_cached(query_string, ps.FETCHONE)
    if el:
        res = el[1]
        if el[2]:
            res = el[2]
        print("RESULT from levenshtein. ", res)

    return get_match_or_redirect(el)


def match_direct(exec_query):
    cur = conn.cursor()
    query_string_fast = cur.mogrify("""select page.page_id,  page.page_title, redirect.rd_title
        from page
        left outer join redirect on redirect.rd_from = page.page_id
        where lower(%s) = lower(page.page_title_with_spaces)
    """, (exec_query, )
    )
    el = postgres_cached(query_string_fast, ps.FETCHONE)
    return get_match_or_redirect(el)


def match_all(exec_query_array):
    cur = conn.cursor()

    exec_query = " ".join(exec_query_array)
    exec_query = s = ''.join(ch for ch in exec_query if ch not in exclude)
    exec_query = " & ".join(exec_query.split())
    # replace all special chars with nothing ascii and then remove everything else
    # exec_query = re.sub(r'[^A-Za-z0-9 ]+', '', exec_query)
    # print(exec_query)
    query_string = cur.mogrify("""select page.page_id, page.page_title, ts_rank(to_tsvector('english', page_title_with_spaces), keywords, 1) as rank
                   from page, to_tsquery(%s) keywords
                   where to_tsvector('english', page_title_with_spaces) @@ keywords
                   ORDER BY rank DESC limit 1""", (exec_query, ))

    return(get_match_or_redirect(postgres_cached(query_string, ps.FETCHONE)))

def match_all_levenshtein(exec_query_array):
    raise NotImplementedError()
    cur = conn.cursor()

    exec_query = " ".join(exec_query_array)
    exec_query = s = ''.join(ch for ch in exec_query if ch not in exclude)
    exec_query = " & ".join(exec_query.split())
    # replace all special chars with nothing ascii and then remove everything else
    # exec_query = re.sub(r'[^A-Za-z0-9 ]+', '', exec_query)
    # print(exec_query)
    query_string = cur.mogrify("""select page.page_id, page.page_title, ts_rank(to_tsvector('english', page_title_with_spaces), keywords, 1) as rank
                   from page, to_tsquery(%s) keywords
                   where to_tsvector('english', page_title_with_spaces) @@ keywords
                   ORDER BY rank DESC limit 1""", (exec_query, ))

    return(get_match_or_redirect(postgres_cached(query_string, ps.FETCHONE)))


def match_or(exec_query_array):
    cur = conn.cursor()

    exec_query = " ".join(exec_query_array)
    exec_query = s = ''.join(ch for ch in exec_query if ch not in exclude)
    exec_query = " | ".join(exec_query.split())
    # replace all special chars with nothing ascii and then remove everything else
    # exec_query = re.sub(r'[^A-Za-z0-9 ]+', '', exec_query)
    # print(exec_query)
    query_string = cur.mogrify("""select page.page_id, page.page_title, ts_rank(to_tsvector('english', page_title_with_spaces), keywords, 1) as rank
                   from page, to_tsquery(%s) keywords
                   where to_tsvector('english', page_title_with_spaces) @@ keywords
                   ORDER BY rank DESC""", (exec_query, ))

    els = postgres_cached(query_string, ps.FETCHALL)
    if els:
        el, match_score = score(exec_query.split(), els)
        # print(el, match_score)
        # TODO: add function to check score height
        return(get_match_or_redirect(el))
