from Tagger import Tagger

import nltk


class NltkTagger(Tagger):
    
    def send_tokens(self, tokens):
        self.buffer += nltk.pos_tag(tokens)



# tagger = NltkTagger()
# tagger.start()
# # tagger.send_text("This is not a sentence. Or, is it? I wish it was; I could perform tagging tests on it.")
# tagger.send_text("This is not a sentence.")
# print(tagger.end())