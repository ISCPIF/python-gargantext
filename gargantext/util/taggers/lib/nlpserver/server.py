#!python3

import pipeline
import socketserver

from settings import server_type_server, server_host, server_port, server_timeout
from settings import b_implemented_methods


actions = {
    b'TAG': pipeline.tag_sentence,
    b'LEMMATIZE': pipeline.tag_lemmatize_sentence,
    b'PARSE': pipeline.parse_sentence,
}

class NLPServer(socketserver.StreamRequestHandler):

    def handle(self):
        # What kind of request are we handling?
        firstline = self.rfile.readline()
        parameters = firstline.split()
        if len(parameters) != 2:
            self.wfile.write(b'\n\n')
            return
        action, language = parameters
        if action not in b_implemented_methods:
            self.wfile.write(b'\n\n')
            return
        # Get the text data
        text = ''
        while True:
            line = self.rfile.readline().decode()
            if not line.strip():
                break
            text += line
            text += '\n'
        # Execute the action
        method = actions.get(action, None)
        if method is None:
            for sentence in pipeline.split_sentences(text):
                for token in pipeline.tokenize(sentence):
                    self.wfile.write(
                        token.encode() + b'\n'
                    )
                self.wfile.write(b'\n')
            self.wfile.write(b'\n')
        else:
            for sentence in pipeline.split_sentences(text):
                for row in method(sentence):
                    self.wfile.write(
                        (
                            '\t'.join(row)
                        ).encode() + b'\n'
                    )
                self.wfile.write(b'\n')
            self.wfile.write(b'\n')

    def handle_timeout(self):
        self.request.sendall(b'\n\n')

        
if __name__ == '__main__':
    print('STARTING TCP SERVER')
    server = server_type_server((server_host, server_port), NLPServer)
    server.timeout = server_timeout
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        print('STOPPING TCP SERVER')
        server.shutdown()
