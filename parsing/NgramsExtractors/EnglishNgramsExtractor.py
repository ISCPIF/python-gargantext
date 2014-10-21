from parsing.NgramsExtractors.NgramsExtractor import NgramsExtractor
from parsing.Taggers import NltkTagger


class EnglishNgramsExtractor(NgramsExtractor):

    def start(self):
        self.tagger = NltkTagger()
        
