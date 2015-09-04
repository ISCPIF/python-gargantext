from .Tagger import Tagger
from .lib.melttagger.tagger import POSTagger, Token, DAGParser, DAGReader

import subprocess
import sys
import os


# references for tag equivalents:
# - http://cs.nyu.edu/grishman/jet/guide/PennPOS.html
# - http://www.lattice.cnrs.fr/sites/itellier/SEM.html
class identity_dict(dict):
    def __missing__(self, key):
        return key
_tag_replacements = dict()
_tag_replacements['fr'] = identity_dict({
    'DET':      'DT',
    'NC':       'NN',
    'NPP':      'NNP',
    'ADJ':      'JJ',
    'PONCT':    '.',
    'ADVWH':    'WRB',
    'ADV':      'RB',
    'DETWH':    'WDT',
    'PROWH':    'WP',
    'ET':       'FW',
    'VINF':     'VB',
    'I':        'UH',
    'CS':       'IN',

    # 'CLS':      '',
    # 'CLR':      '',
    # 'CLO':      '',

    # 'PRO':      '',
    # 'PROREL':   '',
    # 'P':        '',
    # 'P+D':      '',
    # 'P+PRO':    '',

    # 'V':        '',
    # 'VPR':      '',
    # 'VPP':      '',
    # 'VS':       '',
    # 'VIMP':     '',

    # 'PREF':     '',
    # 'ADJWH':    '',
})
_tag_replacements['en'] = identity_dict()


class MeltTagger(Tagger):

    def __init__(self, *args, **kwargs):
        self.language = kwargs.pop('language', 'fr')
        self._tag_replacements = _tag_replacements[self.language]
        super(self.__class__, self).__init__(*args, **kwargs)

    def start(self, melt_data_path='lib/melttagger'):
        language = self.language
        basepath = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(basepath, melt_data_path)
        self._pos_tagger = POSTagger()
        self._pos_tagger.load_tag_dictionary('%s/%s/tag_dict.json' % (path, language))
        self._pos_tagger.load_lexicon('%s/%s/lexicon.json' % (path, language))
        self._pos_tagger.load_model('%s/%s' % (path, language))
        self._preprocessing_commands = (
            ('%s/MElt_normalizer.pl' % path, '-nc', '-c', '-d', '%s/%s' % (path, language), '-l', language, ),
            ('%s/segmenteur.pl' % path, '-a', '-ca', '-af=%s/pctabr' % path, '-p', 'r'),
        )
        self._lemmatization_commands = (
            ('%s/MElt_postprocess.pl' % path, '-npp', '-l', language),
            ('%s/MElt_lemmatizer.pl' % path, '-m', '%s/%s' % (path, language)),
        )

    def stop(self):
        pass

    def _pipe(self, text, commands, encoding='utf8'):
        text = text.encode(encoding)
        for command in commands:
            process = subprocess.Popen(
                command,
                bufsize=0,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            text, err = process.communicate(text)
            if len(err):
                print(err.decode(encoding), file=sys.stderr)
        return text.decode(encoding)

    def _tag(self, text):
        preprocessed = self._pipe(text, self._preprocessing_commands)
        for sentence in preprocessed.split('\n'):
            words = sentence.split(' ')
            tokens = [Token(word) for word in words]
            tagged_tokens = self._pos_tagger.tag_token_sequence(tokens)
            for token in tagged_tokens:
                if len(token.string):
                    yield (token.string, token.label, )

    def tag_text(self, text, lemmatize=False):
        tagged_tokens = self._tag(text)
        # without lemmatization
        if not lemmatize:
            for form, tag in tagged_tokens:
                yield (form, self._tag_replacements[tag])
            return
        # with lemmatization
        command_input = ' '.join(
            '%s/%s' % (token, tag)
            for token, tag in tagged_tokens
        )
        lemmatized = self._pipe(command_input, self._lemmatization_commands)
        for token in lemmatized.split():
            if len(token):
                values = token.split('/')
                yield (values[0], self._tag_replacements[values[1]], values[2].replace('*', ''))
