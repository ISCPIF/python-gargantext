from .Tagger import Tagger
from .nlpserver.client import NLPClient


class TurboTagger:
        
    def start(self):
        self._nlpclient = NLPClient()

    def stop(self):
        del self._nlpclient

    def tag_text(self, text):
        tokens_tags = []
        for sentence in self._nlpclient.tag(text):
            for token, tag in sentence:
                tokens_tags.append((token, tag, ))
        return tokens_tags
