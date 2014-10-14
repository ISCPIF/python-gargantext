import Collections


class FileParser:
    
    def __init__(self, file=None, path=""):
        # initialize output...
        self.text = ""
        self.metadata = {}
        self.ngram_count = Collections.defaultdict(int)
        # ...get contents...
        if file is None:
            file = open(path, "rb")
        self.contents = file.readall()
        # ...parse, then extract the words!
        self.parse()
        self.extract()
    
    def detect_encoding(self, string):
        # see chardet
        pass
    
    def parse(self, contents):
        pass
        
    def extract(self):
        re_sentence = re.compile(r'''(?x) # set flag to allow verbose regexps
            (?:[A-Z])(?:\.[A-Z])+\.? # abbreviations, e.g. U.S.A.
            | \w+(?:-\w+)* # words with optional internal hyphens
            | \$?\d+(?:\.\d+)?%? # currency and percentages, e.g. $12.40, 82%
            | \.\.\. # ellipsis
            | [][.,;"'?():-_`] # these are separate tokens
            ''', re.UNICODE | re.MULTILINE | re.DOTALL)
        for line in self.text.split('\n'):
            for token in re_sentence.findall(line):
                pass
   
   
from EuropressFileParser import EuropressFileParser