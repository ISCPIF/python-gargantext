from .Tagger import Tagger
from .lib.nlpserver.client import NLPClient


class TurboTagger:

    def start(self):
        self._nlpclient = NLPClient()

    def stop(self):
        if hasattr(self, '_nlpclient'):
            del self._nlpclient

    def tag_text(self, text):
        if not hasattr(self, '_nlpclient'):
            self._nlpclient = NLPClient()
        tokens_tags = []
        for sentence in self._nlpclient.tag(text):
            for token, tag in sentence:
                tokens_tags.append((token, tag, ))
        return tokens_tags
