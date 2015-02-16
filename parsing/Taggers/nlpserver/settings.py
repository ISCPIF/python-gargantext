import os
import socket
import socketserver

# Server parameters
server_host = 'localhost'
server_port = 1234
server_type_server = socketserver.TCPServer
server_type_client = socket.AF_INET, socket.SOCK_STREAM
server_timeout = 2.0
server_buffer = 4096

# Implemented methods (other are treated as 'tokenize')
implemented_methods = {'TOKENIZE', 'TAG', 'LEMMATIZE'}
# server_methods = {'TOKENIZE', 'TAG', 'LEMMATIZE', 'PARSE'}
b_implemented_methods = {name.encode() for name in implemented_methods}

# Models
data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
tokenizer_model = os.path.join(data_dir, 'english.pickle')
tagger_model = os.path.join(data_dir, 'english_proj_tagger.model')
# parser_model = 'data/210basic_sd330'
parser_model = os.path.join(data_dir, 'english_proj_parser_pruned-true_model-full.model')
b_tagger_model = tagger_model.encode()
b_parser_model = parser_model.encode()

# Temporary files access
tmp_input_path = '/tmp/nlpserver_input.tmp'
tmp_output_path = '/tmp/nlpserver_output.tmp'
b_tmp_input_path = tmp_input_path.encode()
b_tmp_output_path = tmp_output_path.encode()
