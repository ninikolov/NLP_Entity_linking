import requests
import requests_cache
from fuzzymatch_titles import match_levenshtein, match_or
from pprint import pprint
import marshal
import IPython
all_properties = {}
all_break_words = []

requests_cache.install_cache('wikidata_cache')

WD_URL = 'https://wikidata.org/entity/{entity}.json'
WD_PROP_QUERY = 'https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={entity_title}&languages=en&format=json'
WD_RESULT_QUERY = 'https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={entity_title}&languages=en&format=json'

def init_wikidata():
    global all_break_words
    global all_properties
    try:
        with open('wikidata_properties.pickle', 'rb+') as pickle_file:
            ms = marshal.load(pickle_file)
            all_break_words = ms[0]
            all_properties = ms[1]
    except FileNotFoundError:
        print("No file found ... ")

    with open('wikidata_properties.txt') as wp:
        lines = [line.rstrip('\n') for line in wp.readlines()]
        for line in lines:
            if line not in all_properties:
                res = requests.get(WD_URL.format(entity=line))
                res = res.json()
                for entity in res['entities'].values():

                    break_words = [entity['labels']['en']['value']]
                    if entity.get('aliases') and entity['aliases'].get('en'):
                        break_words += [elem['value'] for elem in entity['aliases']['en']]
                    description = entity['descriptions']['en']['value']

                all_properties[line] = {
                    'break_words': break_words,
                    'description': description
                }

                all_break_words += break_words

    print(all_break_words)

    with open('wikidata_properties.pickle', 'wb+') as pickle_file:
        marshal.dump((all_break_words, all_properties), pickle_file)


def query_wiki(q_a, searched_props):
    print("Searching the schnitzel  w")
    query   = " ".join(q_a)
    print(query)
    res = match_or(q_a)

    print("RESULT: ", res)
    print(WD_PROP_QUERY.format(entity_title=res))
    props = requests.get(WD_PROP_QUERY.format(entity_title=res))
    props = props.json()
    claim = []
    for matched_ent in props['entities'].values():
        claims = matched_ent['claims']
        pprint(claims.keys())
        for searched_prop in searched_props:
            if searched_prop in claims:
                print("WE AHVE SDJ SKDJ SAKDJ SJ JKD J")
                claim  += claims[searched_prop]
                pprint(claims[searched_prop])
    results = []
    if claim:
        for c in claim:
            snak = c['mainsnak']
            if snak['datatype'] == 'item' or snak['datatype'] == 'wikibase-item':
                did = snak['datavalue']['value']['numeric-id']
                res = requests.get(WD_URL.format(entity='Q'+str(did)))
                res = res.json()
                for entity in res['entities'].values():
                    results.append(entity['sitelinks']['enwiki']['title'].replace(' ', '_'))
            elif snak['datatype'] == 'time':
                results.append(snak['datavalue']['value']['time'])
            pprint(results)
    print("This is the result: ", results)
    return results



def find_breakword(elem):
    print(elem)
    for break_word in all_break_words:
        if (elem.startswith(break_word) or break_word.startswith(elem)) and abs(len(elem) - len(break_word)) <= 2:
            print("\n\n\n\n\nLENGHT: ", abs(len(elem) - len(break_word)))
            return break_word
    return None


def check_wiki_data(query_array):
    for elem in query_array:
        bw = find_breakword(elem)
        if bw:
            query_without_breakword = [e for e in query_array if e != elem]
            search_props = []
            for key, val in all_properties.items():
                if bw in val['break_words']:
                    search_props.append(key)
            return query_wiki(query_without_breakword, search_props)


if __name__ == '__main__':
    init_wikidata()
    check_wiki_data("siblings of michael jackson".split())
