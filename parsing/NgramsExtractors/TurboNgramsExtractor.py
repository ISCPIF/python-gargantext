from .NgramsExtractor import NgramsExtractor
from ..Taggers import NltkTagger #TurboTagger 


class TurboNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = NltkTagger()
