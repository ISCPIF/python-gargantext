"""This base class is a model for performing tagging in a pipeline fashion.
When started, it initiates the parser;
when passed text, the text is piped to the parser.
When ended, the parser is closed and the tagged word returned as a tuple.
"""

import re


class Tagger:

    def __init__(self):
        # This regular expression is really good at tokenizing a text!
        self._re_sentence = re.compile(r'''(?x)  # set flag to allow verbose regexps
            (?:[A-Z])(?:\.[A-Z])+\.?        # abbreviations, e.g. U.S.A.
            | \w+(?:-\w+)*                  # words with optional internal hyphens
            | \$?\d+(?:\.\d+)?%?            # currency and percentages, e.g. $12.40, 82%
            | \.\.\.                        # ellipsis
            | [][.,;"'?!():-_`]             # these are separate tokens
            ''', re.UNICODE | re.MULTILINE | re.DOTALL)
        self.buffer = []
        self.start()

    def __del__(self):
        self.stop()

    def start(self):
        """Initializes the tagger.
        This method is called by the constructor, and can be overriden by
        inherited classes.
        """

    def stop(self):
        """Ends the tagger.
        This method is called by the destructor, and can be overriden by
        inherited classes.
        """

    def tagging_start(self):
        """This method is userful in the case of pipelines requiring
        boundaries around blocks of text.
        """

    def tagging_end(self):
        pass

    def tag_tokens(self, tokens, single=True):
        """Returns the tagged tokens.
        This method shall be overriden by inherited classes.
        Example of input: ['This', 'is', 'not', 'a', 'sentence', '.']
        Example of output: [('This', 'DT'), ('is', 'VBZ'), ('not', 'RB'), ('a', 'DT'), ('sentence', 'NN'), ('.', '.')]
        """
        if single:
            self.tagging_start()
        # do something with the tokens here
        if single:
            self.tagging_end()
        return []


    # Not used right now
    def tag_text(self, text):
        """Send a text to be tagged.
        """
        tokens_tags = []
        self.tagging_start()
        for line in text.split('\n'):
            tokens = self._re_sentence.findall(line)
            tokens_tags += self.tag_tokens(tokens, False)
        self.tagging_end()
        return tokens_tags
