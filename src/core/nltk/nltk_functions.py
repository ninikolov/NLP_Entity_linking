"""
NLTK Tokenizer
"""
import nltk

nltk.data.path.append("../lib/nltk_data")

def tag(text):
    tokenized = nltk.word_tokenize(text)
    tagged = nltk.pos_tag(tokenized)

    return tagged


def chunk(text):

    grammar = "NP: {<DT>?<JJ>*<NN>}"
    grammar = """ NP: 
        {<.*>+}
        }<DT|JJ>+{ 
        """

    cp = nltk.RegexpParser(grammar)
    #result = cp.parse(text)

    result = nltk.ne_chunk(text)

    #print(result)
    result.draw()

#s = "types    of  gun used in  violent events"
s = "David the good student came only 10 min late"
print(tag(s))
print(chunk(tag(s)))
