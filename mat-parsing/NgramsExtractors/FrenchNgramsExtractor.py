from NgramsExtractors.NgramsExtractor import NgramsExtractor
from Taggers import TreeTagger


class FrenchNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = TreeTagger()

