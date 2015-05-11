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


def get_most_probable_disambiguation(q):
    entities = q.entities

def wiki_cached_get(ent):
    print(ent)
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

    r = wiki_cached_get(disam_entity)
    if type(r) == DisambiguationError:
        "All is going according to planb"
        print(r.options)
        disambiguation = str(r)
        for d in r.options:
            wk_d = wiki_cached_get(d)
            if type(wk_d) != DisambiguationError:
                ds.append(wk_d)

    e_match = wiki_cached_get(other)

    curr_max_prob = 0
    for d in ds:
        cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (d.summary, " | ".join(other.split())))
        res = cur.fetchone()
        if res[0] > curr_max_prob:
            curr_max_prob = res[0]
            curr_new_ent = d.title

        print(d.title, res)

    print("The selected entity is: ", curr_new_ent)
    return curr_new_ent.replace(' ', '_')

def select_best_entity(entity_collection, other):
    other_entity = wiki_cached_get(other)

    possible_entities = []
    for e_str in entity_collection:
        possible_entities.append(wiki_cached_get(e_str))


    current_res = None
    current_max_prob = 0
    for m in possible_entities:
        other_search = " | ".join(other.replace('_', ' ').split())
        cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.content, other_search))
        res = cur.fetchone()

        if res[0] > current_max_prob:
            current_res = m
            curr_max_prob = res[0]


    if not current_res or current_max_prob == 0:            
        for m in possible_entities:

            c = other_entity.content
            c = re.sub('[^0-9a-zA-Z\s]+', '', c)
            cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.content, " | ".join(c.split())))
            res = cur.fetchone()
            if res[0] > current_max_prob:
                current_res = m
                curr_max_prob = res[0]
    return current_res.title.replace(' ', '_')

            print("FULLFULLTEXTMATCH: " , res)

def main():
    queries = [{
        "entities": ["PNC", "Online_banking"],
        "query": "pnc online banking"
    }]

    ds = []
    #for e in queries[0]['entities']:
    #    r = wiki_cached_get(e)
    #    if type(r) == DisambiguationError:
    #       print(r.options)
    #        disambiguation = str(r)
    #        for d in r.options:
    #            wk_d = wiki_cached_get(d)
    #            if type(wk_d) != DisambiguationError:
    #                ds.append(wk_d)
    #e_match = wiki_cached_get('Online_banking')

    select_best_entity(['Green_laser', 'Viridian Green Laser Sights', 'Sights'], 'Glock')

    # curr_max_prob = 0
    # for d in ds:
    #     cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (d.summary, " | ".join('online banking'.split())))
    #     res = cur.fetchone()
    #     if res[0] > curr_max_prob:
    #         curr_max_prob = res[0]
    #         curr_new_ent = d.title

    #     print(d.title, res)
    # #print("The selected entity is: ", curr_new_ent)

    # m_set_1 = wiki_cached_get('Glock')
    # m_set_2 = [
    #     wiki_cached_get('Green_laser'),
    #     wiki_cached_get('Viridian Green Laser Sights')
    # ]

    # for m in m_set_2:
    #     print(m.content)
    #     cur.execute("select ts_rank(to_tsvector(%s), to_tsquery(%s))", (m.content, " | ".join('glock'.split())))
    #     res = cur.fetchone()
    #     print(m.title, res[0])
if __name__ == "__main__":
    main()
