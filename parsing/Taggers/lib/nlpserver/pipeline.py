from settings import *
from sys import stderr

def print(text):
    stderr.write(text + '\n')

print('PREPARING TURBOPARSER')
import turboparser
turbo_interface = turboparser.PTurboParser()

print('LOADING TOKENIZERS')
import nltk
sentence_tokenizer = nltk.data.load(tokenizer_model)
word_tokenizer = nltk.TreebankWordTokenizer()

if 'TAG' in implemented_methods or 'LEMMATIZE' in implemented_methods:
    print('LOADING TAGGER')
    tagger = turbo_interface.create_tagger()
    tagger.load_tagger_model(b_tagger_model)

if 'LEMMATIZE' in implemented_methods or 'TAG' in implemented_methods or 'PARSE' in implemented_methods:
    print('LOADING LEMMATIZER')
    from lemmatizer import lemmatize

if 'PARSE' in implemented_methods:
    print('LOADING PARSER')
    parser = turbo_interface.create_parser()
    parser.load_parser_model(b_parser_model)


def split_sentences(text):
    return sentence_tokenizer.tokenize(text)

def tokenize(sentence):
    return word_tokenizer.tokenize(sentence)

def tag_sentence(sentence):
    # Write tokens to input file
    f_input = open(tmp_input_path, 'w')
    for token in tokenize(sentence):
        f_input.write(token + '\t_\n')
    f_input.close()
    # Tag tokens
    tagger.tag(b_tmp_input_path, b_tmp_output_path)
    # Iterate through tagged tokens
    f_output = open(tmp_output_path)
    for line in f_output:
        line = line.rstrip('\n')
        if line == '':
            continue
        token, tag = line.split('\t')
        yield (token, tag)
    f_output.close()

def tag_lemmatize_sentence(sentence):
    # Write tokens to input file
    f_input = open(tmp_input_path, 'w')
    for token in tokenize(sentence):
        f_input.write(token + '\t_\n')
    f_input.close()
    # Tag tokens
    tagger.tag(b_tmp_input_path, b_tmp_output_path)
    # Iterate through tagged tokens
    f_output = open(tmp_output_path)
    for line in f_output:
        line = line.rstrip('\n')
        if line == '':
            continue
        token, tag = line.split('\t')
        lemma = lemmatize(token, tag)
        yield (token, tag, lemma)
    f_output.close()

def parse_sentence(sentence):
    # Write tokens to input file
    f_input = open(tmp_input_path, 'w')
    # Iterate through tagged tokens, prepare input
    i = 0
    for token, tag, lemma in tag_lemmatize_sentence(sentence):
        i += 1
        f_input.write(
            # position
            str(i) + '\t' +
            # token
            token + '\t' +
            # lemma
            lemma + '\t' +
            # tag (twice)
            tag + '\t' +
            tag + '\t' +
            # filler
            '_\t_\t_\n'
        )
    f_input.close()
    # Parse sentence
    parser.parse(b_tmp_input_path, b_tmp_output_path)
    # Iterate through parsed stuff
    f_output = open(tmp_output_path)
    for line in f_output:
        line = line.rstrip('\n')
        if line == '':
            continue
        fields = line.split('\t')
        #
        token = fields[1]
        lemma = fields[2]
        tag = fields[3]
        head = str(int(fields[6]) - 1)
        deprel = fields[7]
        yield (token, tag, head, deprel)
