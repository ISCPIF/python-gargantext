from parsing.NgramsExtractors.NgramsExtractor import NgramsExtractor
from parsing.Taggers import TreeTagger


class FrenchNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = TreeTagger()

