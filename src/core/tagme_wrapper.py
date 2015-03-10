"""
TAGME Wrapper
"""

BASE_URL_SCORE = "http://tagme.di.unipi.it/rel?key=tagme-NLP-ETH-2015&lang=en&tt="

from urllib.request import urlopen
import json


def similarity_score(entity1, entity2):
    """
    Get similarity score between two entities through querying the TAGME API.
    :param entity1: string of the entity name, has to match Wiki
    :param entity2: string of the entity name, has to match Wiki
    :return: the similarity score
    """
    assert isinstance(entity1, str)
    assert isinstance(entity2, str)
    response = urlopen(BASE_URL_SCORE + entity1 + "+" + entity2)
    data = json.loads(response.read().decode("utf-8"))
    try:
        score = data['result'][0]['rel']
    except KeyError:
        print("Error in syntax of API request")
    return float(score)


print(similarity_score("ETH_Zurich", "University_of_Zurich"))
print(similarity_score("Justin_Bieber", "Metallica"))
print(similarity_score("Zurich", "Coca-Cola"))