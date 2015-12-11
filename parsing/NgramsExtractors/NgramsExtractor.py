from ..Taggers import NltkTagger
import nltk
from re import sub


"""Base class for all ngrams extractors.
"""
class NgramsExtractor:

    """Class instanciation.
    This method can be overriden.
    
    -*-*-*-*-
    contenus :
    [...'__dict__', '_grammar', '_label', '_rule', 'extract_ngrams', 'start', 'stop', 'tagger']
    
    
    """
    def __init__(self, rule="{<JJ.*>*<NN.*|>+<JJ.*>*}"):
    # TODO add this regex
    #'^((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?(CD.,)??)+?((PREP.?|DET.?,|IN.?,|CC.?,|\?,)((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?)+?)*?$'
        self.start()
        self._label = "NP"
        self._rule = self._label + ": " + rule
        self._grammar = nltk.RegexpParser(self._rule)

    def __del__(self):
        self.stop()

    def start(self):
        self.tagger = NltkTagger()

    def stop(self):
        pass


    """Extracts a list of ngrams.
    Returns a list of the ngrams found in the given text.
    """
    def extract_ngrams(self, contents):
        clean_contents = self._prepare_text(contents)

        # ici tagging
        tagged_tokens = list(self.tagger.tag_text(clean_contents))

        if len(tagged_tokens):
            grammar_parsed = self._grammar.parse(tagged_tokens)
            for subtree in grammar_parsed.subtrees():
                if subtree.label() == self._label:
                    yield subtree.leaves()

    @staticmethod
    def _prepare_text(text_contents):
        """
        Clean the text for better POS tagging
        """
        # strip xml tags
        return sub(r"<[^>]{0,45}>","",text_contents)
