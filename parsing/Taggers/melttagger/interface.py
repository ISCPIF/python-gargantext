melt_data_path = '/usr/local/share/melt/'
melt_package_path = '/usr/local/lib/python2.7/dist-packages/melt/'


import re
import sys
sys.path.append(melt_package_path)

from tagger import POSTagger, Token


class Tagger:

    def __init__(self, language='fr'):
        # load tagger
        path = '%s/%s' % (melt_data_path, language)
        self.pos_tagger = POSTagger()
        self.pos_tagger.load_tag_dictionary('%s/tag_dict.json' % path)
        self.pos_tagger.load_lexicon('%s/lexicon.json' % path)
        self.pos_tagger.load_model('%s' % path)

    def tag(self, words):
        tokens = [
            Token(string=word)
            for word in words
        ]
        for token in self.pos_tagger.tag_token_sequence(tokens):
            # print token.__dict__.keys()
            yield token.string, token.label


language = sys.argv[1].encode() if len(sys.argv) > 1 else 'fr'
tagger = Tagger(language)
while True:
    text = sys.stdin.read()
    if text:
        words = re.findall(r'{(.+?)\}', text)
        for token, tag in tagger.tag(words):
            print '%s\t%s' % (token, tag, )
