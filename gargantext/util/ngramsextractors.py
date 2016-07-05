from gargantext.util.languages import languages
from gargantext.constants import LANGUAGES, DEFAULT_MAX_NGRAM_LEN, RULE_JJNN, RULE_JJPNN

import nltk
import re
class NgramsExtractor:

    def __init__(self, tagger):
        self._tagger = tagger()

    @staticmethod
    def clean_text(text):
        """Clean the text for better POS tagging.
        For now, only removes (short) XML tags.
        """
        return re.sub(r'<[^>]{0,45}>', '', text)

    def extract(self, text, rule=RULE_JJNN, label='NP', max_n_words=DEFAULT_MAX_NGRAM_LEN):
        text = self.clean_text(text)
        grammar = nltk.RegexpParser(label + ': ' + rule)
        tagged_tokens = list(self._tagger.tag_text(text))
        if len(tagged_tokens):
            grammar_parsed = grammar.parse(tagged_tokens)
            for subtree in grammar_parsed.subtrees():
                if subtree.label() == label:
                    if len(subtree) < max_n_words:
                        yield subtree.leaves()
                            # ex: [('wild', 'JJ'), ('pollinators', 'NNS')]


class NgramsExtractors(dict):

    def __missing__(self, key):
        if not isinstance(key, str):
            raise KeyError
        if len(key) == 2 and key == key.lower():
            tagger = LANGUAGES[key]['tagger']
            self[key] = NgramsExtractor(tagger)
        else:
            self[key] = self[LANGUAGES[key].iso3]
        return self[key]


# this below will be shared within the current thread
ngramsextractors = NgramsExtractors()
