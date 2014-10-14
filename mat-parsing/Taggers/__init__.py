class Tagger:

    def start(self):
        self.buffer = []
        
    def send(self, text):
        pass
        
    def end(self):
        return self.buffer

        
from NltkTagger import NltkTagger
from TreeTagger import TreeTagger