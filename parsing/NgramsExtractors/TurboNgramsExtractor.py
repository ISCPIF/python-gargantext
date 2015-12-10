from .NgramsExtractor import NgramsExtractor
from ..Taggers import NltkTagger


class TurboNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = NltkTagger()
