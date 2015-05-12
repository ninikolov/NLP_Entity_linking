import wikipedia as wk
from wikipedia import DisambiguationError
import redis
import pickle
import psycopg2
import sys
import re

# most important ideas:
# remove instance from results (ie. remove PNC Bank Arts Center for less confusion)
# match summaries

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
            raise

def match_disambiguation(disam_entity, other):

    ds = []
    r = wiki_cached_get(disam_entity)
    if type(r) == DisambiguationError:
        disambiguation = str(r)
        for d in r.options:
            ds.append(d)

    return select_best_entity(ds, other)

def select_best_entity(entity_collection, other):
    other_entity = wiki_cached_get(other)

    possible_entities = []
    for e_str in entity_collection:
        if not type(wiki_cached_get(e_str)) == DisambiguationError:
            possible_entities.append(wiki_cached_get(e_str))

    current_res = None
    current_max_prob = 0

    for m in possible_entities:

        other_search = " | ".join(other.replace('_', ' ').split())
        # print(m.summary)
        cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.summary, other_search))
        res = cur.fetchone()
        print(res[0], current_max_prob)
        if res[0] > current_max_prob:
            current_res = m.title
            current_max_prob = res[0]


    if not current_res or current_max_prob == 0:
        # Match against content
        current_max_prob = 0

        for m in possible_entities:

            c = other_entity.content
            c = re.sub('[^0-9a-zA-Z\s]+', '', c)

            cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.content, other_search))
            res = cur.fetchone()

            if res[0] > current_max_prob:
                current_res = m.title
                current_max_prob = res[0]

    return current_res.replace(' ', '_')


def main():

    ds = []

    a = match_disambiguation('PNC', 'online banking')
    print(a)
    # b = select_best_entity(['Green_laser', 'Viridian Green Laser Sights'], 'Glock')
    # print(b)

if __name__ == "__main__":
    main()
