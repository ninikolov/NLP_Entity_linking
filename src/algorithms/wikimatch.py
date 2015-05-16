import wikipedia as wk
from wikipedia import DisambiguationError, PageError
import redis
import pickle
import psycopg2
import sys
import re
from .fuzzy_helper import match_direct
# most important ideas:
# remove instance from results (ie. remove PNC Bank Arts Center for less confusion)
# match summaries
import enchant 

d = enchant.Dict("en_US")

r = redis.StrictRedis(host='localhost', port=6379, db=1)

psql = psycopg2.connect("dbname=mw user=wolfv")
cur = psql.cursor()


def wiki_cached_get(ent):
    if r.exists(ent):
        return pickle.loads(r.get(ent))
    else:
        try:
            res = wk.page(ent)
            r.set(ent, pickle.dumps(res))
            return res
        except DisambiguationError as e:
            r.set(ent, pickle.dumps(e))
            return e
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("While looking for: ", ent)
            # raise
            return None

def get_disam_list(page_id):
    ds = []
    if page_id.lower() == 'va':
        print("VA: \n\n\n\n\n\n")
        print(wiki_cached_get(page_id))

    try:
        r = wiki_cached_get(page_id)
    except PageError as e:
        print("Whoops, no page", str(e))
        return ds
    print(str(r))
    if type(r) == DisambiguationError:
        disambiguation = str(r)
        for d in r.options:
            ds.append(d)
    return ds


def match_disambiguation(disam_entity, other):
    ds = get_disam_list(disam_entity)
    if not ds:
        ds = get_disam_list(disam_entity + '_(disambiguation)')
    if not ds:
        get_disam_list(disam_entity.upper())
    
    print(str(r))

    return select_best_entity(ds, other)

def select_best_entity(entity_collection, other):
    # other_entity = wiki_cached_get(other)

    possible_entities = []
    for e_str in entity_collection:
        try:
            r = wiki_cached_get(e_str)
            if r and not type(r) == DisambiguationError:
                possible_entities.append(wiki_cached_get(e_str))
        except PageError as e:
            print("Well, this page doesn't exist: ", str(e))

    current_res = None
    current_max_prob = 0


    new_entities = []
    for m in possible_entities:

        other_search = " | ".join(other.replace('_', ' ').split())
        # print(m.summary)
        cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.summary, other_search))
        res = cur.fetchone()
        print(res[0], current_max_prob)
        new_entities.append((m.title.replace(' ', '_'), res[0]))
        if res[0] > current_max_prob:
            current_res = m.title
            current_max_prob = res[0]


    # if not current_res or current_max_prob == 0:
    #     # Match against content
    #     current_max_prob = 0

    #     for m in possible_entities:

    #         c = other_entity.content
    #         c = re.sub('[^0-9a-zA-Z\s]+', '', c)

    #         cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.content, other_search))
    #         res = cur.fetchone()

    #         if res[0] > current_max_prob:
    #             current_res = m.title
    #             current_max_prob = res[0]
    if new_entities:
        new_entities.sort(key=lambda x: x[1], reverse=True)
        print(new_entities)
        return new_entities

    # if current_res and current_max_prob > 0:
    #     return current_res.replace(' ', '_')
    else:
        return None

from nltk.corpus import stopwords
stop = stopwords.words('english')

def handle_queries(q):

    matches = []
    wo_stops = [el for el in q.array if el not in stop]
    for idx, el in enumerate(wo_stops):
        if len(el) < 5 or el.isupper():
            if len(el) > 2 and d.check(el):
                # Word is in dictionary
                continue
            cont = False
            for i in range(idx + 1, len(wo_stops)):
                if match_direct(" ".join(wo_stops[idx:i])):
                    cont = True
                    break
            if cont:
                continue
            entity = match_direct(el)
            if entity:
                matches.append((el, match_disambiguation(entity, " ".join([e for e in q.array if e != el]))))
            else:
                matches.append((el, match_disambiguation(el, " ".join([e for e in q.array if e != el]))))


    return matches




def main():

    ds = []

    a = match_disambiguation('PNC', 'online banking')
    print(a)
    # b = select_best_entity(['Green_laser', 'Viridian Green Laser Sights'], 'Glock')
    # print(b)

if __name__ == "__main__":
    main()
