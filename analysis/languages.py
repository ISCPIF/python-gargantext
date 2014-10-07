# coding: utf-8

import nltk
#import analysis.treetaggerwrapper as tt

# ENGLISH

def english_pos_tag(sentance):
    words = nltk.word_tokenize(sentance)
    t = nltk.pos_tag(words)
    return(t)

def english_stem(word):
    from nltk.stem.snowball import EnglishStemmer
    stemmer = EnglishStemmer()
    return(stemmer.stem(word))


# FRENCH 

"""
Now TreeTagger
Next Stanford for licence reason
See : https://github.com/cmchurch/nltk_french/blob/master/french-nltk.py
"""

def get_postag(tags):
    """
    TreeTagger translation
    """
    x_v=tags.split('\t')
    
    if len(x_v)==3:
        term = term_comp=x_v[2]
        if term == "<unknown>":
            term =' '.join(map(lambda y: y.split('|')[-1], x_v[0].split(' ')))
            
        return (term,x_v[1].split(':')[0]\
                .replace('NOM','NN')\
                .replace('NAM','NN')\
                
                .replace('ADJ','JJ')\
                .replace('VER','VV')\
                .replace('PREP','PRP')\
                .replace('KON','CC')\
                
                .replace('DET','DT')\
                .replace('PRO','DT'))
    else:
        x=x.replace('<','').replace('>','')
        return (x,u'unknown')

def tag(tags):
    """
    Return a list of 
    """
    arbre = []
    for i in tags:
        data = get_postag(i)
        arbre.append(data)
    return(arbre)

def french_pos_tag(sentance):
    tagger = tt.TreeTagger(\
        TAGLANG='fr',\
        TAGDIR='/home/alexandre/projets/gargantext.py/gargantext_core/shared/treetagger/',\
        TAGINENC='utf-8',\
        TAGOUTENC='utf-8')
    tags = tagger.TagText(sentance)
    t = tag(tags)
    return(t)

def french_stem(word):
    from nltk.stem.snowball import FrenchStemmer
    stemmer = FrenchStemmer()
    return(stemmer.stem(word))

# GERMAN

# SPANISH
