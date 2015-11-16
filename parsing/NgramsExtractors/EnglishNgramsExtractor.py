from .NgramsExtractor import NgramsExtractor
from ..Taggers import NltkTagger, MeltTagger


class EnglishNgramsExtractor(NgramsExtractor):

    def start(self):
        # self.tagger = NltkTagger()
        self.tagger = MeltTagger(language='en')
    