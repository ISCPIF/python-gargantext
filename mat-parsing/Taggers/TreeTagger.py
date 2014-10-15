from Tagger import Tagger

import subprocess
import threading
import time


# TODO: have a look at "queue" instead of "list" (cf. http://stackoverflow.com/questions/17564804/in-python-how-to-wait-until-only-the-first-thread-is-finished)

class identity_dict(dict):
    def __missing__(self, key):
        return key
    
_tag_replacements = identity_dict({
    "NOM": "NN",
    "NAM": "NN",
    "ADJ": "NN",
    "VER": "JJ",
    "PREP": "PRP",
    "KON": "CC",
    "DET": "DT",
    "PRO": "DT",
    # Do we also have to take semicolons, comas and other points into account?
})


def _readOutput(output, buffer):
    while True:
        line = output.readline()
        if line:
            if line == b"<end/>\n":
                break
            token, tag = line.decode('utf8').split()[:2]
            tag = _tag_replacements[tag.split(':')[0]]
            buffer.append((token, tag))
        else:
            time.sleep(0.1)


"""Use TreeTagger for the tagging.
Shall be used for french texts.
"""
class TreeTagger(Tagger):
    
    def start(self, treeTaggerPath = "../../../nlp/pythonwrapperP3/treetagger"):
        binaryFile = "%s/bin/tree-tagger" % treeTaggerPath
        tagcmdlist = [
            binaryFile,
            "%s/lib/french-utf8.par" % treeTaggerPath,
            "-token",
            "-lemma",
            "-sgml",
            "-quiet"
        ]
        self._popen = subprocess.Popen(
            tagcmdlist,     # Use a list of params in place of a string.
            bufsize=0,      # Not buffered to retrieve data asap from TreeTagger
            executable=binaryFile, # As we have it, specify it
            stdin=subprocess.PIPE,  # Get a pipe to write input data to TreeTagger process
            stdout=subprocess.PIPE, # Get a pipe to read processing results from TreeTagger
            stderr=subprocess.PIPE, # Get a pipe to read processing results from TreeTagger
        )
        self._input, self._output = self._popen.stdin, self._popen.stdout
        # self._thread = threading.Thread(target=_readOutput, args=(self._output, self.buffer, )).start()
        self._thread = threading.Thread(target=_readOutput, args=(self._output, self.buffer, ))
        self._thread.start()
        
    def send_tokens(self, tokens):
        for token in tokens:
            self._input.write(bytes(token + "\n", "utf8"))
    
    def end(self):
        # send some dummy tokens, then wait for the text to be treated
        self.send_tokens("<end/> Les sanglots longs des violons de l ' automne bercent mon coeur d ' une langueur monotone .".split())
        # wait for the thread to end
        self._thread.join()
        # terminates the 'treetagger' process
        self._popen.kill()
        self._popen.terminate()
        # returns the tagged tokens
        return self.buffer


# tagger = TreeTagger()
# tagger.start()
# tagger.send_text("Ceci n'est pas une phrase, n'est-ce pas? Parfois, il faut tester des phrases ; mêmes celles avec des points-virgules.")
# print(tagger.end())