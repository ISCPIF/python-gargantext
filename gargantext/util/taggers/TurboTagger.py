# from ._Tagger import Tagger
from .lib.nlpserver.client import NLPClient


class TurboTagger:

    def start(self):
        self._nlpclient = NLPClient()
        #self.extract(self.text)

    def stop(self):
        if hasattr(self, '_nlpclient'):
            del self._nlpclient

    def extract(self, text):
        if not hasattr(self, '_nlpclient'):
            self._nlpclient = NLPClient()
        try:
            tokens_tags = []
            for sentence in self._nlpclient.tag(text):
                for token, tag in sentence:
                    tokens_tags.append((token, tag, ))
            return tokens_tags
        except ConnectionRefusedError as e:
            print(e)
            print("TurboTagger: problem with the NLPServer (try running gargantext/parsing/Taggers/lib/nlpserver/server.py)")
            # TODO abort workflow?
            return []
