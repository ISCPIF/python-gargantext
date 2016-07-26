#!/usr/bin/python env
from ._Tagger import Tagger
#from nltk import pos_tag
from nltk.tag.perceptron    import PerceptronTagger

class NltkTagger(Tagger):
    '''Require maxtree'''
    #import nltk
    def __init__(self, *args, **kwargs):
        self.tagr =  PerceptronTagger()
        super(self.__class__, self).__init__(*args, **kwargs)

    #~ def __start__(self):
        #~ self.tagr =  PerceptronTagger()

    def tag_tokens(self, tokens, single=True):
        return self.tagr.tag(tokens)
