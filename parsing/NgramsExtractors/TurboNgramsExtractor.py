from .NgramsExtractor import NgramsExtractor
from ..Taggers import NltkTagger
# from ..Taggers import TurboTagger 


class TurboNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = NltkTagger()
        # self.tagger = TurboTagger()
