"""
NLTK Tokenizer
"""
import nltk
import inflection
from nltk.corpus import wordnet as wn


nltk.data.path.append("../../../data/nltk_data")

def tag(text):
    tokenized = nltk.word_tokenize(text)
    tagged = nltk.pos_tag(tokenized)
    return tagged


def nounify(verb_word):
    """ Transform a verb to the closest noun: die -> death """
    verb_synsets = wn.synsets(verb_word, pos="v")

    # Word not found
    if not verb_synsets:
        return []
    # Get all verb lemmas of the word
    verb_lemmas = [l for s in verb_synsets \
                   for l in s.lemmas() if s.pos() == 'v']

    # Get related forms
    derivationally_related_forms = [(l, l.derivationally_related_forms()) \
                                    for l in verb_lemmas]

    # filter only the nouns
    related_noun_lemmas = [l for drf in derivationally_related_forms \
                           for l in drf[1] if l.synset().pos() == 'n']

    # Extract the words from the lemmas
    words = [inflection.humanize(l.synset().name().split('.')[0]).lower() for l in related_noun_lemmas]
    len_words = len(words)

    # Build the result in the form of a list containing tuples (word, probability)
    result = [(w, float(words.count(w)) / len_words) for w in set(words)]
    result.sort(key=lambda w: -w[1])
    # return all the possibilities sorted by probability
    return result


def soft_fix(query_str):
    """Clean common query problems"""
    query_str = query_str.replace("'", " ")
    query_str = query_str.replace(" s ", " ")
    query_str = query_str.replace(" s", " ")
    query_str = query_str.replace("s ", " ")
    query_str = "".join(c for c in query_str if c not in ('!', ':', ',', '\'', '"', '?'))
    query_str = query_str.strip().lower()
    return query_str


def hard_fix(query_str, convert=True):
    """Go further than the above function,
    convert all adjectives and verbs to nouns
    singularise all nouns"""
    # query_str = " ".join(inflection.singularize(word) for word in query_str.split())
    # query_str = query_str.replace(".", " ")
    query_str = query_str.replace("'", " ")
    query_str = query_str.replace(" s ", " ")
    query_str = query_str.replace(" s", " ")
    query_str = query_str.replace("s ", " ")
    query_str = "".join(c for c in query_str if c not in ('!', ':', ',', '\'', '"', '?'))
    if convert:
        tokenized = nltk.word_tokenize(query_str)
        tags = nltk.pos_tag(tokenized)
        final_query = ""
        for item in tags:
            t = item[1]
            if t.startswith("NN"):  # noun
                final_query += " " + inflection.singularize(item[0])
            elif t.startswith("JJ") or t.startswith("VB"):  # adj or verb
                subs = nounify(item[0])
                if subs:
                    noun = nounify(item[0])[0][0]
                    final_query += " " + noun
                else:
                    final_query += " " + item[0]
            else:
                final_query += " " + item[0]
        query_str = final_query
    query_str = query_str.strip().lower()
    return query_str


def chunk(text):

    grammar = "NP: {<DT>?<JJ>*<NN>}"
    grammar = """ NP: 
        {<JJ>*<NP|NN|NNP><NP|NN|NNP><NP|NN|NNP>}
        }<IN|DT>+{ 
        """

    cp = nltk.RegexpParser(grammar)
    result = cp.parse(text)

    #result = nltk.ne_chunk(text)

    return result
    #result.draw()

def get_array(var):
    """get an array of words from a chunk  """
    array = []
    if(type(var) is nltk.tree.Tree):
        for (word, tag) in var:
            array.append(word)
    elif (type(var) is tuple):
        assert(len(var)==2)
        array.append(var[0])
    return(array)

if __name__ == '__main__':
    # s = "types    of  gun used in  violent events"
    s = "policies for addressing economic problems in europe"
    s2 = "legality alcohol history marijuana"
    tags = tag(s)
    print(tags)
    # print(chunk(tag(s)))
    print(nounify("paint"))
