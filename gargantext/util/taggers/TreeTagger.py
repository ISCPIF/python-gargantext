from ._Tagger import Tagger

import subprocess
import threading
import time
import os


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
    hasStarted = False
    while True:
        line = output.readline()
        if line:
            if line == b"<block>\n":
                hasStarted = True
                continue
            if line == b"<block/>\n":
                break
            if hasStarted:
                token, tag = line.decode('utf8').split()[:2]
                tag = _tag_replacements[tag.split(':')[0]]
                buffer.append((token, tag))
        else:
            time.sleep(0.1)


class TreeTagger(Tagger):

    """Use TreeTagger for the tagging.
    Shall be used for french texts.
    """

    def start(self, treeTaggerPath='./lib/treetagger'):
        print(treeTaggerPath)
        if treeTaggerPath[0] == '.':
            treeTaggerPath = '%s/%s' % (os.path.dirname(os.path.realpath(__file__)), treeTaggerPath, )
            print(treeTaggerPath)
        binaryFile = "%s/bin/tree-tagger" % (treeTaggerPath, )
        print(binaryFile)
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
        # self.buffer = OutputBuffer()

    def stop(self):
        # terminates the 'treetagger' process
        try:
            self._popen.kill()
            self._popen.terminate()
        except:
            pass

    def tagging_start(self):
        self.buffer = []
        self._thread = threading.Thread(target=_readOutput, args=(self._output, self.buffer, ))
        self._thread.start()
        self._input.write(b"<block>\n")

    def tagging_end(self):
        self._input.write(b"<block/>\n")
        # sends some dummy tokens, then wait for the text to be treated
        self.tag_tokens("Les sanglots longs des violons de l ' automne bercent mon coeur d ' une langueur monotone .".split(), False)
        self._thread.join()


    def tag_tokens(self, tokens, single=True):
        if single:
            self.tagging_start()
        for token in tokens:
            self._input.write(bytes(token + "\n", "utf8"))
        if single:
            self.tagging_end()
            return self.buffer

    def tag_text(self, text):
        self.tagging_start()
        for line in text.split('\n'):
            tokens = self._re_sentence.findall(line)
            self.tag_tokens(tokens, False)
        self.tagging_end()
        return self.buffer
