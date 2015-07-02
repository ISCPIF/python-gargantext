from .NgramsExtractor import NgramsExtractor
from ..Taggers import TreeTagger


class FrenchNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = TreeTagger()
        # self.tagger = MeltTagger(language='fr')
