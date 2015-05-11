from .Tagger import Tagger
from .melttagger.tagger import POSTagger, Token, DAGParser, DAGReader

import subprocess
import sys
import os


# references for tag equivalents:
# - http://cs.nyu.edu/grishman/jet/guide/PennPOS.html
# - http://www.lattice.cnrs.fr/sites/itellier/SEM.html
class identity_dict(dict):
    def __missing__(self, key):
        return key
_tag_replacements = identity_dict({
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


class MeltTagger(Tagger):

    def start(self, language='fr', melt_data_path='melttagger'):
        basepath = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(basepath, melt_data_path, language)
        self._pos_tagger = POSTagger()
        self._pos_tagger.load_tag_dictionary('%s/tag_dict.json' % path)
        self._pos_tagger.load_lexicon('%s/lexicon.json' % path)
        self._pos_tagger.load_model('%s' % path)
        self._preprocessing_commands = (
            # ('/usr/local/bin/clean_noisy_characters.sh', ),
            # ('/usr/local/bin/MElt_normalizer.pl', '-nc', '-c', '-d', '/usr/local/share/melt/normalization/%s' % language, '-l', language, ),
            ('/usr/local/share/melt/segmenteur.pl', '-a', '-ca', '-af=/usr/local/share/melt/pctabr', '-p', 'r'),
        )
        self._lemmatization_commands = (
            ('/usr/local/bin/MElt_postprocess.pl', '-npp', '-l', language),
            ('MElt_lemmatizer.pl', '-m', '/usr/local/share/melt/%s' % language),
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
                    yield (token.string, _tag_replacements[token.label], )

    def tag_text(self, text, lemmatize=True):
        tagged_tokens = self._tag(text)
        if not lemmatize:
            for tagged_token in tagged_tokens:
                yield tagged_token
            return
        # lemmatization
        command_input = ' '.join(
            '%s/%s' % (token, tag)
            for token, tag in tagged_tokens
        )
        lemmatized = self._pipe(command_input, self._lemmatization_commands)
        for token in lemmatized.split():
            if len(token):
                values = token.split('/')
                yield (values[0], values[1], values[2].replace('*', ''))
