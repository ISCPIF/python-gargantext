from configparser import RawConfigParser
from decouple import AutoConfig, RepositoryIni


class GargantextIni(RepositoryIni):
    SECTION = 'django'

    def __init__(self, source):
        self.parser = RawConfigParser()
        with open(source) as file_:
            self.parser.readfp(file_)


class GargantextConfig(AutoConfig):
    SUPPORTED = {'gargantext.ini': GargantextIni}


config = GargantextConfig(search_path='.')
