from Taggers import Tagger
import nltk


"""Base class for all ngrams extractors.
"""
class NgramsExtractor:

    """Class instanciation.
    This method can be overriden.
    """
    def __init__(self, rule="NP: {<JJ.*>*<NN.*|>+<JJ.*>*}"):
        self.start()
        self._rule = rule
        
    def __del__(self):
        self.stop()
        
        
    def start(self):
        self.tagger = Tagger
        
    def stop(self):
        pass
        
    
    """Extracts a list of ngrams.
    Returns a list of the ngrams found in the given text.
    """
    def extract_ngrams(self, contents):
        tagged_ngrams = self.tagger.tag_text(contents)
        grammar = nltk.RegexpParser(self._rule)
        result = []
        try:
            grammar_parsed = grammar.parse(tagged_ngrams)
            grammar_parsed_iterator = grammar_parsed.subtrees()

            while True:
                try:
                    subtree = next(grammar_parsed_iterator)
                    if subtree.label() == 'NP':
                        #print(subtree.label())
                        result.append(subtree.leaves())

                except Exception as e:
                    break

        except Exception as e:
            print(e)
            pass
        return iter(result)
        
        
    