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
        if len(tagged_ngrams)==0: return []
        
        grammar = nltk.RegexpParser(self._rule)
        result = []
        # try:
        grammar_parsed = grammar.parse(tagged_ngrams)
        for subtree in grammar_parsed.subtrees():
            if subtree.label() == self._label:
                result.append(subtree.leaves())
        # except Exception as e:
        #     print("Problem while parsing rule '%s'" % (self._rule, ))
        #     print(e)
        return result
        
        
    
