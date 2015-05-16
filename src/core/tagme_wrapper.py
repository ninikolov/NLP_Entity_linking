"""
Wrapper for the TAGME API http://tagme.di.unipi.it
"""

BASE_URL_SCORE = "http://tagme.di.unipi.it/rel?key=tagme-NLP-ETH-2015&lang=en&tt="
url = "http://tagme.di.unipi.it/rel"
tag_url = "http://tagme.di.unipi.it/tag"
wiki_synonyms_url = "http://wikisynonyms.ipeirotis.com/api/"

import json
import os
import sys

import requests
from core.query import SearchQuery, SearchMatch, Entity


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from core.query import Entity
import requests_cache

requests_cache.install_cache('../../data/tagme-cache')

def similarity_score(entity1, entity2):
    """
    Get similarity score between two entities through querying the TAGME API.
    :param entity1: string of the entity name, has to match Wiki
    :param entity2: string of the entity name, has to match Wiki
    :return: the similarity score
    """
    assert isinstance(entity1, Entity)
    assert isinstance(entity2, Entity)
    params = {'key': 'tagme-NLP-ETH-2015', 'lang': 'en', 'tt': entity1.link + " " + entity2.link}
    request = requests.get(url, params=params)
    data = json.loads(request.text)
    try:
        score = data['result'][0]['rel']
    except KeyError:
        score = 0.
    return float(score)


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]


def similarity_score_batch(target_entity, entities, ignore_missing=False):
    """
    Compute similarity score in batch, for a single target entity
    :param target_entity:
    :param entities: list of other entities to score against
    :return:
    """
    assert isinstance(entities, list)
    assert isinstance(target_entity, Entity)
    scores = []
    if not entities:
        return scores
    params = {'key': 'tagme-NLP-ETH-2015', 'lang': 'en', 'tt': [target_entity.link + " " + e.link for e in entities]}
    request = requests.get(url, params=params)
    try:
        data = json.loads(request.text)
    except ValueError:
        # print("Wrong output returned for ", request.url, ". Maybe URI too large?")
        # Try again with shorter URLs
        print("URL: ", request.url)
        for sublist in split_list(entities, wanted_parts=3):
            scores += similarity_score_batch(target_entity, sublist)
        return scores
    error_count = 0
    result = data['result']
    result_sz = len(result)
    assert len(entities) == result_sz
    for i in range(result_sz):
        res = result[i]
        try:
            scores.append(float(res['rel']))
        except KeyError:
            error_count += 1
            # print("error for ", res)
            if ignore_missing:
                scores.append(0.)
            else:
                scores.append(None)
    # if error_count > 0:
    #    print(error_count, " erros in syntax of API request - ", request.url)
    return scores


def position(query, start_ch):
    """
    Calculate position of word
    :param query:
    :param start_ch:
    :param end_ch:
    :return:
    """
    q_array = query.split()
    curr = 0
    start = -1
    for w_ind in range(len(q_array)): # word
        for l_ind in range(len(q_array[w_ind])): # letter
            #print(l_ind + curr + 1)
            if l_ind + curr + 1 < start_ch:
                continue
            else:
                start = w_ind
        curr += len(q_array[w_ind]) + 1
    try:
        assert start >= 0
    except AssertionError:
        print(q_array, len(query), start_ch, curr)
        raise AssertionError
    return start

def tag(query):
    """
    Used for the second baseline. Tag query using the TAGME API.
    :param query_str:
    :return:
    """
    params = {'key': 'tagme-NLP-ETH-2015', 'lang': 'en', 'text': query.search_string}
    request = requests.get(tag_url, params=params)
    data = json.loads(request.text)
    for ann in data['annotations']:
        pos = position(query.search_string, ann['start'])
        e = ann['title'].replace(" ", "_")
        match = SearchMatch(pos, len(ann['spot'].split()), [Entity(e, 1.)], ann['spot'])
        match.chosen_entity = 0
        query.add_match(match)

if __name__ == '__main__':
    # print(similarity_score(Entity("Carlyle,_Illinois", 0.), Entity("Dam_(disambiguation)", 0.)))
    # print(similarity_score(Entity("Broadcasting", 0.), Entity("Anchor_&_Braille", 0.)))
    # print(similarity_score("Justin_Bieber", "Metallica"))
    # print(similarity_score("Zurich", "Coca-Cola"))
    # print(check_synonym("Nicki_Minaj"))
    tag("eth zurich")
    # print(position("eth zurich", 5, 8))