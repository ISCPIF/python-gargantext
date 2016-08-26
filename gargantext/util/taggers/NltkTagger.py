#!/usr/bin/python env
from ._Tagger import Tagger
#from nltk import pos_tag
from nltk.tag.perceptron    import PerceptronTagger

class NltkTagger(Tagger):
    '''Require maxtree'''
    #import nltk
    def __init__(self, *args, **kwargs):
        self.tagr =  PerceptronTagger()
        #super(self.__class__, self).__init__(*args, **kwargs)

    #def __start__(self):
        #~ self.tagr =  PerceptronTagger()

    def tag_tokens(self, tokens, single=True):
        return self.tagr.tag(tokens)

    # def extract(self, text, rule=RULE_JJNN, label='NP', max_n_words=DEFAULT_MAX_NGRAM_LEN):
    #     self.text = self.clean_text(text)
    #     grammar = nltk.RegexpParser(label + ': ' + rule)
    #     tagged_tokens = list(self.tag_text(self.text))
    #     if len(tagged_tokens):
    #         grammar_parsed = grammar.parse(tagged_tokens)
    #         for subtree in grammar_parsed.subtrees():
    #             if subtree.label() == label:
    #                 if len(subtree) < max_n_words:
    #                     yield subtree.leaves()
    #                         # ex: [('wild', 'JJ'), ('pollinators', 'NNS')]
