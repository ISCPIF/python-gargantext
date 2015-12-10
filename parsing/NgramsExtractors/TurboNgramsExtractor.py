from .NgramsExtractor import NgramsExtractor
from ..Taggers import TurboTagger #NltkTagger


class TurboNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = TurboTagger()
