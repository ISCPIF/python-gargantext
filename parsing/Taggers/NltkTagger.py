from .Tagger import Tagger

import nltk


class NltkTagger(Tagger):
    
    def tag_tokens(self, tokens, single=True):
        return nltk.pos_tag(tokens)

