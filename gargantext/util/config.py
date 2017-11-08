import os
from configparser import RawConfigParser
from decouple import AutoConfig, RepositoryIni


SEARCH_PATH, GARGANTEXT_CONF = \
    os.path.split(os.environ.get('GARGANTEXT_CONF', 'gargantext.ini'))


class GargantextIni(RepositoryIni):
    SECTION = 'django'

    def __init__(self, source):
        self.parser = RawConfigParser()
        with open(source) as file_:
            self.parser.readfp(file_)


class GargantextConfig(AutoConfig):
    SUPPORTED = {GARGANTEXT_CONF: GargantextIni}


config = GargantextConfig(search_path=SEARCH_PATH or '.')
