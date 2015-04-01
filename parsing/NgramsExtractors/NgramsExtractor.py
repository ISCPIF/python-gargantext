from ..Taggers import TurboTagger
import nltk


"""Base class for all ngrams extractors.
"""
class NgramsExtractor:

    """Class instanciation.
    This method can be overriden.
    """
    def __init__(self, rule="{<JJ.*>*<NN.*|>+<JJ.*>*}"):
        self.start()
        self._label = "NP"
        self._rule = self._label + ": " + rule
        self._grammar = nltk.RegexpParser(self._rule)
        
    def __del__(self):
        self.stop()
        
    def start(self):
        self.tagger = TurboTagger()
        
    def stop(self):
        pass
        
    
    """Extracts a list of ngrams.
    Returns a list of the ngrams found in the given text.
    """
    def extract_ngrams(self, contents):
        tagged_ngrams = self.tagger.tag_text(contents)
        if len(tagged_ngrams):
            grammar_parsed = self._grammar.parse(tagged_ngrams)
            for subtree in grammar_parsed.subtrees():
                if subtree.label() == self._label:
                    yield subtree.leaves()
