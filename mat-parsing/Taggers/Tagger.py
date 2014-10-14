import re


"""This regular expression is really good at tokenizing a text!
"""
_re_sentence = re.compile(r'''(?x)  # set flag to allow verbose regexps
    (?:[A-Z])(?:\.[A-Z])+\.?        # abbreviations, e.g. U.S.A.
    | \w+(?:-\w+)*                  # words with optional internal hyphens
    | \$?\d+(?:\.\d+)?%?            # currency and percentages, e.g. $12.40, 82%
    | \.\.\.                        # ellipsis
    | [][.,;"'?!():-_`]             # these are separate tokens
    ''', re.UNICODE | re.MULTILINE | re.DOTALL)


"""This class is a model for performing tagging in a pipeline fashion.
When started, it initiates the parser;
when passed text, the text is piped to the parser.
When ended, the parser is closed and the tagged word returned
in a tuple format.
"""
class Tagger:

    def __init__(self):
        self.buffer = []
    
    """Initialize the tagger.
    This method shall be overriden by inherited classes.
    """
    def start(self):
        pass

    """Send a list of tokens to be tagged.
    This method shall be overriden by inherited classes.
    """
    def send_tokens(self, tokens):
        pass
        
    """Send a text to be tagged.
    """
    def send_text(self, text):
        for line in text.split('\n'):
            self.send_tokens(
                _re_sentence.findall(line)
            )
    
    """Ends the tagger and returns the tagged tokens.
    This method shall be overriden by inherited classes.
    Example of output: [('The', 'DET'), ('dog', 'NOM'), ('is', 'VER'), ('green', 'ADJ'), ('.', 'PUN')]
    """
    def end(self):
        return self.buffer
    
    """Starts the tagger, pipes the text,
    ends the tagger, returns the result.
    """
    def tag(self, text):
        self.start()
        self.send_text(text)
        return self.end()
        
