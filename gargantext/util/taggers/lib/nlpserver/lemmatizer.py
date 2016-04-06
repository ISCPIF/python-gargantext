from nltk.stem import WordNetLemmatizer
from collections import defaultdict

lemmatizer = WordNetLemmatizer()
_lemmatize = lemmatizer.lemmatize
tags_translate = defaultdict(str)
tags_translate.update({
    'J': 'a',
    'N': 'n',
    'V': 'v',
})

def lemmatize(token, tag):
    tag_type = tags_translate[tag[0]]
    return _lemmatize(token, tag_type) if tag_type else token

