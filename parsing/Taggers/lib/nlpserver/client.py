import socket
import sys
import re

from .settings import server_type_client, server_host, server_port, server_buffer
from .settings import implemented_methods


class NLPClient:

    def __init__(self):
        self._socket = None
        for method_name in dir(self):
            if method_name[0] != '_':
                if method_name.upper() not in implemented_methods:
                    setattr(self, method_name, self._notimplemented)

    def __del__(self):
        self._disconnect()

    def _connect(self):
        self._disconnect()
        self._socket = socket.socket(*server_type_client)
        self._socket.connect((server_host, server_port))

    def _disconnect(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def _notimplemented(self, *args, **kwargs):
        raise NotImplementedError(
            'Only the following methods are allowed: {}'.format(
                ', '.join(implemented_methods)
            )
        )

    def _getline(self):
        """Get one line of text from the buffer
        """
        buf = self._socket.recv(server_buffer).decode()
        done = False
        while not done:
            if '\n' in buf:
                line, buf = buf.split('\n', 1)
                yield line
            else:
                more = self._socket.recv(server_buffer).decode()
                if not more:
                    done = True
                else:
                    buf += more
        if buf:
            yield buf

    def _request(self, action, text, language, keys=None):
        """Generic method to request info from the server
        """
        if text is None:
            return
        data = action + ' '
        data += language + '\n'
        data += re.sub(r'\n+', '\n', text)
        data += '\n\n'
        self._connect()
        self._socket.sendall(data.encode())
        sentence = []
        if keys is None:
            for line in self._getline():
                if not line:
                    if not sentence:
                        break
                    yield sentence
                    sentence = []
                    continue
                sentence.append(line.split('\t'))
        else:
            for line in self._getline():
                if not line:
                    if not sentence:
                        break
                    yield sentence
                    sentence = []
                    continue
                values = line.split('\t')
                sentence.append(dict(zip(keys, line.split('\t'))))

    def tokenize(self, text, language='english', asdict=False):
        keys = ('token', ) if asdict else None
        return self._request('TOKENIZE', text, language, keys)

    def tag(self, text, language='english', asdict=False):
        keys = ('token', 'tag', ) if asdict else None
        return self._request('TAG', text, language, keys)

    def lemmatize(self, text, language='english', asdict=False):
        keys = ('token', 'tag', 'lemma') if asdict else None
        return self._request('LEMMATIZE', text, language, keys)

    def parse(self, text, language='english', asdict=False):
        keys = ('token', 'tag', 'lemma', 'head', 'deprel', ) if asdict else None
        return self._request('PARSE', text, language, keys)


# Benchmark when the script is called directly
if __name__ == '__main__':
    from time import time
    text = """Current therapeutics for schizophrenia, the typical and atypical antipsychotic class of drugs, derive their therapeutic benefit predominantly by antagonism of the dopamine D2 receptor subtype and have robust clinical benefit on positive symptoms of the disease with limited to no impact on negative symptoms and cognitive impairment. Driven by these therapeutic limitations of current treatments and the recognition that transmitter systems beyond the dopaminergic system in particular glutamatergic transmission contribute to the etiology of schizophrenia significant recent efforts have focused on the discovery and development of novel treatments for schizophrenia with mechanisms of action that are distinct from current drugs. Specifically, compounds selectively targeting the metabotropic glutamate receptor 2/3 subtype, phosphodiesterase subtype 10, glycine transporter subtype 1 and the alpha7 nicotinic acetylcholine receptor have been the subject of intense drug discovery and development efforts. Here we review recent clinical experience with the most advanced drug candidates targeting each of these novel mechanisms and discuss whether these new agents are living up to expectations."""
    text = open('/home/mat/projects/parser/animal-farm.txt').read()
    client = NLPClient()
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for asdict in (False, True):
        print()
        print('Retrieving results as ' + (
            'dict' if asdict else 'list'
        ) + 's')
        print('---------------------------')
        for method_name in dir(client):
            if method_name[0] != '_':
                method = getattr(client, method_name)
                print('%-16s' % method_name, end='')
                t0 = time()
                n = 0.0
                for i in range(0, iterations):
                    try:
                        for sentence in method(text, asdict=asdict):
                            n += 1.0
                        t = time() - t0
                        print('%8.2f s %8.2f ms per sentence' % (t, 1000*t/n if n else 0.0))
                    except NotImplementedError:
                        print('(not implemented)')
    print()
    
    # lemmatize           2.89 s     1.76 ms per sentence
    # parse              25.21 s    15.37 ms per sentence
    # tag                 2.90 s     1.77 ms per sentence
    # tokenize            0.19 s     0.12 ms per sentence
