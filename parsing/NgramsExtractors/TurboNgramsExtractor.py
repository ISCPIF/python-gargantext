from .NgramsExtractor import NgramsExtractor
from ..Taggers import TurboTagger


class TurboNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = TurboTagger()
