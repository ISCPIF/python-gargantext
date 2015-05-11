#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
## Copyright (C) 2009 Pascal Denis and Benoit Sagot
## 
## This library is free software; you can redistribute it and#or
## modify it under the terms of the GNU Lesser General Public
## License as published by the Free Software Foundation; either
## version 3.0 of the License, or (at your option) any later version.
## 
## This library is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public
## License along with this library; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#################################################################################

import os
import sys
import re
import math
import tempfile
import codecs
import operator
import time
import optparse 
import unicodedata
import subprocess
from collections import defaultdict


WD_TAG_RE = re.compile(r'^(.+)/([^\/]+)$')
CAPONLYLINE_RE = re.compile(r'^([^a-z]+)$')
number = re.compile("\d")
hyphen = re.compile("\-")
equals = re.compile("=")
upper = re.compile("[A-Z]")
allcaps = re.compile("^[A-Z]+$")

try:
    import numpy as np
except ImportError:
    sys.exit('This module requires that numpy be installed') 

# Import Psyco if available
try:
    import psyco
    psyco.full()
except ImportError:
    pass

try:
    from cjson import dumps, loads
except ImportError:
    try:
        from simplejson import dumps, loads
    except ImportError:
        from json import dumps, loads


# ###### USAGE AND OPTIONS ######

# usage = "usage: %prog [options] <input_file>"
# parser = optparse.OptionParser(usage=usage)
# parser.add_option("-m", "--model", action="store", help="model directory", default="./data")
# parser.add_option("-t", "--train", action="store", help="training data file")
# parser.add_option("-b", "--beam_size", action="store", help="set beam size (default: 3)", type=int, default=3)
# parser.add_option("-e", "--encoding", action="store", help="language encoding (default: utf-8)", default="utf-8")
# parser.add_option("-r", "--repeat", action="store", help="set the number of successive MegaM runs (multiclass only, default: 5)", type=int, default=5)
# parser.add_option("-M", "--maxit", action="store", help="set the number of MegaM iterations per run (default: 100)", type=int, default=100)
# parser.add_option("-C", "--classifier", action="store", help="select the type of classifier to use: multiclass (multiclass MaxEnt, default) or multitron (multiclass perceptron)", type=str, default="multiclass")
# parser.add_option("-p", "--prior_prec", action="store", help="set precision of gaussian prior", type=int, default=1)
# parser.add_option("-d", "--tag_dict", action="store", help="read in tag dictionary", default='')
# parser.add_option("-l", "--lexicon", action="store", help="read in Lexicon DB", default='')
# parser.add_option("-o", "--output_file", action="store", help="output file", default='')
# parser.add_option("-g", "--gold_file", action="store", help="reference file", default='')
# parser.add_option("-c", "--handle_comments", action="store_true", help="handle SxPipe-like comments while tagging", dest="handle_comments", default=False)
# parser.add_option("-P", "--print_probas", action="store_true", help="print the probability of the tag along to the tag itself", dest="print_probas", default=False)
# parser.add_option("-f", "--feature_selection", action="store", help="feature selection options", type=str, default="")
# parser.add_option("-L", "--lowercase_uppercase_sentences", action="store_true", help="lowercase sentences that are fully uppercase", dest="lowercase_uppercase_sentences", default=False)
# parser.add_option("-D", "--dump_raw_model", action="store_true", help="dump the raw MegaM model in the <model_name>.rawmodel file", dest="dump_raw_model", default=False)
# parser.add_option("-Z", "--ZH", action="store_true", help="Chinese mode : train on weighted exemples and decoding on DAG in SXPipe format ", dest="ZH", default=False)
# parser.add_option("-T", "--dump_training_data", action="store_true", help="dump the training data <model_name>.trainingdata file", dest="dump_training_data", default=False)
# (options, args) = parser.parse_args()

# infile = codecs.getreader(options.encoding)(sys.stdin)
# if len(args) > 0:
#     infile = codecs.open( args[0], "r", options.encoding )
# outfile = codecs.getwriter(options.encoding)(sys.stdout)
# if options.output_file:
#     outfile = codecs.open( options.output_file, "w", options.encoding )
# if options.ZH:
#     import sxparser as sxp
#     from DagInstance import DagInstance


# # extra options dict for feature selection
# feat_select_options = { 
#     # default values
#     'win':2, # context window size
#     'lex_wd':1, # lefff current word features
#     'lex_lhs':1, # lefff LHS context features
#     'lex_rhs':1, # lefff RHS context features
#     } 
# if options.feature_selection:
#     for f_opt in options.feature_selection.split(","):
#         name, value = f_opt.split("=")
#         feat_select_options[name] = eval(value)





############################ pos_tagger.py ############################

class POSTagger:


    def __init__(self):
        self.tag_dict = {}
        self.lex_dict = {}
        self.classifier = MaxEntClassifier()
        self.cache = {} 
        return


    def load_model(self, model_path):
        try:
            self.classifier.load( model_path )
        except Exception as e:
            sys.exit("Error: Failure load POS model from %s (%s)" %(model_path,e))
        return


    def train_model(self,_file, model_path, prior_prec=1, maxit=100, repeat=5, classifier="multitron", feat_options={}, dump_raw_model=False,dump_training_data=False,zh_mode = False):
        print("  TAGGER (TRAIN): Generating training data...          ", end=' ', file=sys.stderr)
        reader = "Brown"
        if zh_mode :
            reader = "Weighted"
        train_inst_file = self.generate_training_data( _file,
                                                       feat_options=feat_options,
                                                       dirpath=model_path,   
                                                       dump_training_data=dump_training_data,
                                                       Reader=reader)
        print("  TAGGER (TRAIN): Generating training data: done          ", file=sys.stderr)
        print("  TAGGER (TRAIN): Training POS model...", file=sys.stderr)
        self.classifier.train_megam( train_inst_file,
                                     repeat=repeat,
                                     classifier=classifier,
                                     maxit=maxit,
                                     prior_prec=prior_prec,
                                     dump_raw_model=dump_raw_model,
                                     dirpath=model_path)
        print("  TAGGER (TRAIN): Dumping model in %s" %model_path, file=sys.stderr)
        self.classifier.dump( model_path )
        print("  TAGGER (TRAIN): Clean-up data file...", file=sys.stderr)
        os.unlink(train_inst_file)
        print("done.", file=sys.stderr) 
        return
    

    def generate_training_data(self, infile, feat_options={}, encoding='utf-8',dirpath="MElt_tmp_dir",dump_training_data=False,Reader="Brown"):
        data_file_name = tempfile.mktemp()
        data_file = codecs.open(data_file_name,'w',encoding)
        if dump_training_data:   
            data_dump_file = codecs.open(dirpath+".trainingdata",'w',encoding)
        inst_ct = 0
        if Reader == "Brown":
            CorpusR = BrownReader
        if Reader == "Weighted":
            CorpusR = WeightedReader
        for s in CorpusR(infile):
            # build token list for each sentence (urgh! FIXME)
            tokens = []
            if Reader == "Weighted" :
                weight,s = s
            for wd,tag in s:
                token = Token( string=wd, pos=tag )
                token.label = token.pos # label is POS tag
                tokens.append( token )
            # create training instance for each token
            for i in range(len(tokens)):
                inst_ct += 1
                os.write(1, "%s" %"\b"*len(str(inst_ct))+str(inst_ct))
                inst = Instance( label=tokens[i].label,\
                                 index=i, tokens=tokens,\
                                 feat_selection=feat_options,\
                                 lex_dict=self.lex_dict,\
                                 tag_dict=self.tag_dict,\
                                 cache=self.cache )
                inst.get_features()
                if Reader == "Weighted":
                    print(inst.weighted_str(weight), file=data_file)
                else :
                    print(inst.__str__(), file=data_file)
                    if dump_training_data:   
                        print(inst.__str__(), file=data_dump_file)
                    # print >> sys.stderr, inst.__str__().encode('utf8')
        os.write(1,'\n')
        data_file.close()
        if dump_training_data:   
             data_dump_file.close()
        return data_file_name
    


    def tag_token_sequence(self, tokens, feat_options={}, beam_size=3):
        ''' N-best breath search for the best tag sequence for each sentence'''
        # maintain N-best sequences of tagged tokens
        sequences = [([],0.0)]  # log prob.
        for i,token in enumerate(tokens):
            n_best_sequences = []
            # cache static features
            cached_inst = Instance( label=tokens[i].label,
                                    index=i, tokens=tokens,
                                    feat_selection=feat_options,
                                    lex_dict=self.lex_dict,
                                    tag_dict=self.tag_dict,
                                    cache=self.cache )
            cached_inst.get_static_features()
            # get possible tags: union of tags found in tag_dict and
            # lex_dict
            wd = token.string
            wasCap = token.wasCap
            legit_tags1 = self.tag_dict.get(wd,{})
#            legit_tags2 = self.lex_dict.get(wd,{}) 
            legit_tags2 = {} # self.lex_dict.get(wd,{}) 
#            print >> sys.stderr, "legit_tags1: ", [t for t in legit_tags1]
            for j,seq in enumerate(sequences):
                seq_j,log_pr_j = sequences[j]
                tokens_j = seq_j+tokens[i:] # tokens with previous labels
                # classify token
                inst = Instance( label=tokens[i].label,
                                 index=i, tokens=tokens_j, 
                                 feat_selection=feat_options,
                                 lex_dict=self.lex_dict,
                                 tag_dict=self.tag_dict,
                                 cache=self.cache )
                inst.fv = cached_inst.fv[:]
                inst.get_sequential_features()
                label_pr_distrib = self.classifier.class_distribution(inst.fv)
                # extend sequence j with current token
                for (cl,pr) in label_pr_distrib:
                    # make sure that cl is a legal tag
                    if legit_tags1 or legit_tags2:
                        if (cl not in legit_tags1) and (cl not in legit_tags2):
                            continue
                    labelled_token = Token(string=token.string,pos=token.pos,\
                                           comment=token.comment,\
                                           wasCap=wasCap,\
                                           label=cl,proba=pr,label_pr_distrib=label_pr_distrib)
                    n_best_sequences.append((seq_j+[labelled_token],log_pr_j+math.log(pr)))
            # sort sequences
            n_best_sequences.sort( key=operator.itemgetter(1) )
            #debug_n_best_sequence(n_best_sequences)
            # keep N best
            sequences = n_best_sequences[-beam_size:]
        # return sequence with highest prob. 
        best_sequence = sequences[-1][0]
        # print >> sys.stderr, "Best tok seq:", [(t.string,t.label) for t in best_sequence]
        return best_sequence

        
    def tag_token_dag(self, tokens, feat_options={}, beam_size=3):
        ''' N-best breath search for the best tag sequence for each sentence with segmentation ambiguities'''
        # maintain N-best sequences of tagged tokens
        sequences = [([],0.0)]  # log prob.
        end_index = max([tok.position[1] for tok in tokens])
        while True:
            #on conserve les sequences arrivées au bout
            n_best_sequences = [x for x in sequences if len(x[0])>0 and x[0][-1].position[1]==end_index]
            #optimisation possible
            last_indexes = [ s[0][-1].index  for s in sequences if len(s[0])>0 ]
            if last_indexes == [] :
                last_indexes = [None]
            suivants = set([tok for i in last_indexes for tok in suivants_in_dag(tokens,i)])
            
            if len(suivants) == 0 :
                break
            # cache static features
            for suivant in suivants :
                i = suivant.index
                #cached_inst = DagInstance( label=tokens[i].label,
                #                    index=i, tokens=tokens,
                #                    feat_selection=feat_options,
                #                    lex_dict=self.lex_dict,
                #                    tag_dict=self.tag_dict,
                #                    cache=self.cache )
                #cached_inst.get_static_features()
                ## get possible tags: union of tags found in tag_dict and
                # lex_dict
                wd = suivant.string
                wasCap = suivant.wasCap
                legit_tags1 = self.tag_dict.get(wd,{})
 #               legit_tags2 = self.lex_dict.get(wd,{}) 
                legit_tags2 = {} # self.lex_dict.get(wd,{}) 
 #               print >> sys.stderr, "legit_tags1: ", [t for t in legit_tags1]
                for j,seq in enumerate(sequences):
                    seq_j,log_pr_j = sequences[j]
                    if len(seq_j) > 0 and seq_j[-1].position[1] != suivant.position[0] :
                        continue
                    tokens_j = seq_j+filter_tokens(tokens,i) # tokens with previous labels
                    
                    
                    # classify token
                    inst = DagInstance( label=tokens[i].label,
                                     index=len(seq_j), tokens=tokens_j, 
                                     feat_selection=feat_options,
                                     lex_dict=self.lex_dict,
                                     tag_dict=self.tag_dict,
                                     cache=self.cache )
                    #inst.fv = cached_inst.fv[:]
                    inst.get_static_features()
                    inst.get_sequential_features()
                    label_pr_distrib = self.classifier.class_distribution(inst.fv)
#                    import IPython
#                    IPython.embed()
                    # extend sequence j with current token
                    for (cl,pr) in label_pr_distrib:
                        # make sure that cl is a legal tag
                        if legit_tags1 or legit_tags2:
                            if (cl not in legit_tags1) and (cl not in legit_tags2):
                                continue
                        labelled_token = Token(string=suivant,pos=suivant.pos,\
                                       comment=suivant.comment,\
                                       wasCap=wasCap,\
                                       position=suivant.position,\
                                       index=suivant.index,\
                                       label=cl,proba=pr,label_pr_distrib=label_pr_distrib)
                        n_best_sequences.append((seq_j+[labelled_token],log_pr_j+math.log(pr)))
            # sort sequences
            n_best_sequences.sort( key=lambda x:x[1]/len(x[0]))# operator.itemgetter(1) )
            debug_n_best_sequence(n_best_sequences)
            # keep N best
            sequences = n_best_sequences[-beam_size:]
        # return sequence with highest prob. 
        best_sequence = sequences[-1][0]
        #print >> sys.stderr, "Best tok seq:", [(t.string,t.label) for t in best_sequence]
        return best_sequence


    def apply(self, infile, outfile=None, handle_comments=False, print_probas=False, feat_options={}, beam_size=3, lowerCaseCapOnly=False,zh_mode=False):
        if zh_mode :
            return self.apply_on_DAG(infile, outfile, print_probas, feat_options, beam_size)
        print("  TAGGER: POS Tagging...", file=sys.stderr)
        t0 = time.time()
        # process sentences
        s_ct = 0
        if (handle_comments):
            comment_re = re.compile(r'^{.*} ')
            split_re = re.compile(r'(?<!\}) ')
            token_re = re.compile(r'(?:{[^}]*} *)?[^ ]+')
        else:
            split_re = re.compile(r' ')
            token_re = re.compile(r'[^ ]+')
        for line in infile:
            line = line.strip(' \n')
            wasCapOnly = 0
            if (lowerCaseCapOnly and len(line) > 10):
                wasCapOnly = CAPONLYLINE_RE.match(line)
            if (wasCapOnly):
                wasCapOnly = 1
            else:
                wasCapOnly = 0
            if (wasCapOnly):
                line = line.lower()
#                print >> sys.stderr, "CAPONLY: "+line                
            wds = []
#            wds = split_re.split(line)
            result = token_re.match(line)
            while (result):
                wds.append( result.group() )
                line = token_re.sub("",line,1)
                line = line.strip(' \n')
                result = token_re.match(line)
            tokens = []
            if (handle_comments):
                for wd in wds:
                    result = comment_re.match(wd)
                    if (result):
                        wd = comment_re.sub("",wd)
                        token = Token( string=wd, comment=result.group(), wasCap=wasCapOnly )
                    else:
                        comment = ""
                        token = Token( string=wd, wasCap=wasCapOnly )
                    tokens.append( token )
            else:
                for wd in wds:
                    token = Token( string=wd, wasCap=wasCapOnly )
                    tokens.append( token )
            tagged_tokens = self.tag_token_sequence( tokens,
                                                     feat_options=feat_options,
                                                     beam_size=beam_size )
            if (print_probas):
                tagged_sent = " ".join( [tok.__pstr__() for tok in tagged_tokens] )
            else:
                tagged_sent = " ".join( [tok.__str__() for tok in tagged_tokens] )
            print(tagged_sent, file=outfile)
        print("  TAGGER: POS Tagging: done (in %s sec)." %(time.time()-t0), file=sys.stderr)
        return

    def apply_on_DAG(self, infile, outfile, print_probas, feat_options={}, beam_size=3):
        print("  TAGGER: POS Tagging (a DAG)...", file=sys.stderr)
        t0 = time.time()
        # process sentences
        s_ct = 0
        
        for dag in DAGReader(infile):
            tokens = []
            for i,wd in enumerate(dag):
                    token = Token( string=wd, index=i )
                    tokens.append( token )
            tagged_tokens = self.tag_token_dag( tokens,
                                                     feat_options=feat_options,
                                                     beam_size=beam_size )
            if (print_probas):
                tagged_sent = " ".join( [tok.__pstr__() for tok in tagged_tokens] )
            else:
                tagged_sent = " ".join( [tok.__str__() for tok in tagged_tokens] )
            print(tagged_sent, file=outfile)
        print("  TAGGER: POS Tagging: done (in %s sec)." %(time.time()-t0), file=sys.stderr)
        return

    def load_tag_dictionary(self, filepath ):
        print("  TAGGER: Loading tag dictionary...", file=sys.stderr)
        self.tag_dict = unserialize( filepath )
        print("  TAGGER: Loading tag dictionary: done", file=sys.stderr)
        return


    def load_lexicon(self, filepath ):
        print("  TAGGER: Loading external lexicon...", file=sys.stderr)
        self.lex_dict = unserialize( filepath )
        print("  TAGGER: Loading external lexicon: done", file=sys.stderr)
        return
    



############################ corpus_reader.py ############################


class CorpusReader:
    pass


class BrownReader(CorpusReader):

    """
    Data reader for corpus in the Brown format:

    Le/DET prix/NC de/P vente/NC du/P+D journal/NC n'/ADV a/V pas/ADV <E9>t<E9>/VPP divulgu<E9>/VPP ./PONCT 
    Le/DET cabinet/NC Arthur/NPP Andersen/NPP ,/PONCT administrateur/NC judiciaire/ADJ du/P+D titre/NC depuis/P l'/DET effondrement/NC de/P l'/DET empire/NC Maxwell/NPP en/P d<E9>cembre/NC 1991/NC ,/PO
    NCT a/V indiqu<E9>/VPP que/CS les/DET nouveaux/ADJ propri<E9>taires/NC allaient/V poursuivre/VINF la/DET publication/NC ./PONCT 

    """

    def __init__(self,infile, encoding='utf-8'):
        self.stream = codecs.open(infile, 'r', encoding)
        return

    def __iter__(self):
        return self

    def next(self,lowerCaseCapOnly=0):
        line = self.stream.readline()
        if (line == ''):
            self.stream.seek(0)
            raise StopIteration
        line = line.strip(' \n')
        wasCapOnly = 0
        if (lowerCaseCapOnly == 1 and len(line) > 10):
            wasCapOnly = CAPONLYLINE_RE.match(line)
        token_list = []
        for item in line.split(' '):
            wdtag = WD_TAG_RE.match(item)
            if (wdtag):
                wd,tag = wdtag.groups()
                if (wasCapOnly):
                    token_list.append( (wd.lower(),tag) )
                else:
                    token_list.append( (wd,tag) )
            else:
                print("Warning: Incorrect token/tag pair: \""+item+"\"", file=sys.stderr)
        return token_list





#if __name__ == "__main__":
#    import sys 
#    for s in BrownReader( sys.argv[1] ):
#        print s
####################Weigthed Corpus########################

class WeightedReader(CorpusReader):
    def __init__(self,infile,encoding='utf8'):
        self.stream = codecs.open(infile, 'r', encoding)
        return
    def __iter__(self):
        return self
    def __next__(self):
        line = self.stream.readline().strip()
        if (line == ''):
            self.stream.seek(0)
            raise StopIteration
        weight,tokens = line.split("\t",1)
        w = 1. / float(weight)
        tokens = [ tuple(tok.rsplit("_",1)) for tok in tokens.split() ]
        return (w,tokens)
###########################DAGReader#######################

from .sxparser import sxyacc

class DAGReader(CorpusReader):
    def __init__(self,infile, encoding='utf8'):
        if type(infile) == str or type(infile) == str :
            self.stream = codecs.open(infile,'r',encoding)
            self.allowSeek = True
        else :
            self.allowSeek = False #(peut être stdin)
            self.stream = infile
        return
        
    def __iter__(self):
        return self
    def __next__(self):
        line = self.stream.readline()
        if (line == ''):
            if self.allowSeek:
                self.stream.seek(0)
            raise StopIteration
        dag = sxyacc.parse(line.strip())
        l = sxp.fsa_of_dag(dag)
        return l

class DAGParser(CorpusReader):
    def __init__(self, text, encoding='utf8'):
        self.lines = text.split('\n')
        self.count = len(self.lines)
        self.index = 0
        
    def __iter__(self):
        return self
    def __next__(self):
        if self.index >= self.count:
            raise StopIteration
        line = self.lines[self.index] + '\n'
        self.index += 1
        dag = sxyacc.parse(line.strip())
        l = sxp.fsa_of_dag(dag)
        return l
    

############################ my_token.py ############################


class Token:

    def __init__(self, string=None, wasCap=0, pos=None, label=None, proba=None, comment=None, label_pr_distrib=[],index=None,position=None):
        if type(string) is tuple and isinstance(string[2],sxp.Token) : #DAG
            self.string = string[2].forme
            self.position = tuple(string[0:2])
            self.tokobj = string[2]
        elif isinstance(string,Token) :
            self.string = string.string
            self.position = string.position
            self.tokobj = string.tokobj
        else :
            self.position = position
            self.string = string
            self.comment = comment
        self.index = index
        self.wasCap = wasCap
        self.pos = pos
        self.label = label
        self.proba = proba
        self.comment = comment
        self.label_pr_distrib = label_pr_distrib
        if (self.comment == None):
            self.comment = ""
        return

    def set_label(self, label):
        self.label = label
        return

    def __str__(self):
        if hasattr(self, 'tokobj'):
            r = ""
            if self.tokobj.commentaire != "":
                r += "{%s} " %(self.tokobj.commentaire,)
            r += "%s__%s" %(self.string,self.label)
            if self.tokobj.semantique != "":
                r += "[|%s|] " %(self.tokobj.semantique,)
            return r
        if (self.wasCap):
            return "%s%s/%s" %(self.comment,self.string.upper(),self.label)
        else:
            return "%s%s/%s" %(self.comment,self.string,self.label)

    def __pstr__(self):
        if (self.wasCap):
            return "%s%s/%s/%s" %(self.comment,self.string.upper(),self.label,self.proba)
        else:
            return "%s%s/%s/%s" %(self.comment,self.string,self.label,self.proba)





############################ classifier.py ############################


class MaxEntClassifier:

    def __init__( self ):
        self.classes = []
        self.feature2int = {}
        self.weights = np.zeros( (0,0) )
        self.bias_weights = np.zeros( (0,0) )
        return


    def load(self, dirpath ):
        print("  TAGGER: Loading model from %s..." %dirpath, file=sys.stderr)
        self.classes = unserialize( os.path.join(dirpath, 'classes.json') )
        self.feature2int = unserialize( os.path.join(dirpath, 'feature_map.json') )
        self.weights = np.load( os.path.join(dirpath, 'weights.npy3') )
        self.bias_weights = np.load( os.path.join(dirpath, 'bias_weights.npy3') )
        print("  TAGGER: Loading model from %s: done" %dirpath, file=sys.stderr)
        return


    def dump(self, dirpath):
        print("Dumping model in %s..." %dirpath, end=' ', file=sys.stderr)
        serialize( self.classes, os.path.join(dirpath, 'classes.json') )
        serialize( self.feature2int, os.path.join(dirpath, 'feature_map.json') )
        self.weights.dump( os.path.join(dirpath, 'weights.npy') )
        self.bias_weights.dump( os.path.join(dirpath, 'bias_weights.npy') )
        print("done.", file=sys.stderr)
        return

 

    def train_megam( self, datafile, prior_prec=1, repeat=5, classifier="multitron", maxit=100, bias=True, dump_raw_model=False, dirpath="MElt_tmp_dir" ):
        
        if os.environ.get("MEGAM_DIR",None) == "":
            megam_exec_path = where_is_exec("megam.opt")
            if megam_exec_path == "":
                megam_exec_path = where_is_exec("megam.exe")
                if megam_exec_path == "":
                    sys.exit("Missing env variable for MEGAM_DIR. You need Megam to train models. The MEGAM_DIR variable must be set in your environment and store the path to the directory that contains the megam.opt executable")
        else:
            if os.access(os.environ.get("MEGAM_DIR",None), os.F_OK):
                if os.access(os.environ.get("MEGAM_DIR",None)+"/megam.opt", os.F_OK):
                    megam_exec_path = os.environ.get("MEGAM_DIR",None)+"/megam.opt"
                elif os.access(os.environ.get("MEGAM_DIR",None)+"/megam.exe", os.F_OK):
                    megam_exec_path = os.environ.get("MEGAM_DIR",None)+"/megam.exe"
                else:
                    sys.exit("Could not find megam.opt or megam.exe within the folder specified in the MEGAM_DIR environment variable. You need Megam to train models. The MEGAM_DIR variable must be set in your environment and store the path to the directory that contains the megam.opt or megam.exe executable")
            else:
                sys.exit("The folder specified in the MEGAM_DIR environment variable could not be found. You need Megam to train models. The MEGAM_DIR variable must be set in your environment and store the path to the directory that contains the megam.opt or megam.exe executable")

        if not os.access(os.environ.get("MEGAM_DIR",None)+"/megam.opt", os.X_OK):
            sys.exit("The version of megam (.opt or .exe) that was found is not executable, or you don't have the permissions for executing it. You need Megam to train models. The MEGAM_DIR variable must be set in your environment and store the path to the directory that contains the megam.opt or megam.exe executable")


        """ simple call to Megam executable for multiclass
        classification with some relevant options:
        
        -prior_prec: precision of Gaussian prior (megam default:1). It's
         the inverse variance. See http://www.cs.utah.edu/~hal/docs/daume04cg-bfgs.pdf.
        -repeat: repeat optimization <int> times (megam default:1)
        -maxit: max # of iterations (megam default:100)
        """        

        print("  TAGGER (TRAIN): Training Megam classifier (using "+megam_exec_path+")...", file=sys.stderr)        
        # build process command
        proc = [megam_exec_path, "-nc", "-repeat", repeat, "-lambda", prior_prec, "-maxi", maxit]
        if not bias:
            proc.append("-nobias") 
        proc.append(classifier) # optimization type: multitron / multiclass
        proc.append(datafile)
        print(proc, file=sys.stderr)
        proc = list(map(str,proc))
        # run process
        p = subprocess.Popen(proc, stdout=subprocess.PIPE)
        (outdata, errdata) = p.communicate()
        # check return code
        if p.returncode != 0: 
            print(errdata, file=sys.stderr) 
            raise OSError("Error while trying to execute "+" ".join(proc))
        if dump_raw_model:
            raw_model_file = open(dirpath+".rawmodel", 'w')
            raw_model_file.write(outdata)
            raw_model_file.close
        # load model from megam output
        self.process_megam( outdata )
        # print basic model info
        print("# of classes: %s" %len(self.classes), file=sys.stderr)
        print("# of features: %s" %len(self.feature2int), file=sys.stderr)
        return 




    def process_megam( self, megam_str, encoding="utf-8" ):
        ''' process megam parameter file --- only supports multiclass
        named classes at the moment'''
        nc_str = "***NAMEDLABELSIDS***" 
        bias_str = "**BIAS**"
        lines = megam_str.strip().split('\n')
        # set classes
        line = lines[0]
        if line.startswith(nc_str):
            self.classes = list(map( str, line.split()[1:] ))
            lines.pop(0)
        else:
            raise OSError("Error while reading Megam output: %s not class line" %line) 
        # bias weights
        line = lines[0]
        if line.startswith(bias_str):
            items = line.split()
            self.bias_weights = np.array( list(map(float, items[1:])) )
            lines.pop(0)
        else:
            self.bias_weights = np.zeros( (len(lines),len(self.classes)) ) 
        # set feature map and weight matrix
        self.weights = np.zeros( (len(lines),len(self.classes)) )            
        for i,line in enumerate(lines):
            items = line.strip().split()
            fname = items[0]
            self.feature2int[fname] = i
            self.weights[i] = np.array( list(map(float, items[1:])) )
        return 



    def categorize( self, features ):
        """ sum over feature weights and return class that receives
        highest overall weight 
        """
        weights = self.bias_weights
        for f in features:
            fint = self.feature2int.get(f,None)
            if not fint:
                continue
            fweights = self.weights[fint]
            # summing bias and fweights
            weights = weights+fweights
        # find highest weight sum
        best_weight = weights.max()
        # return class corresponding to highest weight sum
        best_cl_index = np.nonzero(weights == best_weight)[0][0] 
        return self.classes[best_cl_index]



    def class_distribution( self, features ):
        """ probability distribution over the different classes
        """
        # print >> sys.stderr, "event: %s" % features
        weights = self.bias_weights
        for f in features:
            fint = self.feature2int.get(f,None)
            if fint is None:
                continue
            fweights = self.weights[fint]
            # summing bias and fweights
            weights = weights+fweights
        # exponentiation of weight sum
        scores = list(map( math.exp, list(weights) ))
        # compute normalization constant Z
        z = sum( scores )
        # compute probabilities
        probs = [ s/z for s in scores ]
        # return class/prob map
        return list(zip( self.classes, probs ))



############################ instance.py ############################


class Instance:

    def __init__(self, index, tokens, label=None, lex_dict={}, tag_dict={},
                 feat_selection={}, cache={}):
        self.label = label
        self.fv = []
        self.feat_selection = feat_selection
        # token 
        self.token = tokens[index]
        self.index = index
        self.word = self.token.string
        # lexicons
        self.lex_dict = lex_dict
        self.tag_dict = tag_dict  
        self.cache = cache ## TODO
        # contexts
        win = feat_selection.get('win',2) # TODO: different wins for different types of contexts
        self.context_window = win
        self.set_contexts( tokens, index, win )
        return


    def set_contexts(self, toks, idx, win):
        lconx = toks[:idx][-win:]
        rconx = toks[idx+1:][:win]
        self.left_wds = [tok.string for tok in lconx]
        if len(self.left_wds) < win:
            self.left_wds = ["<s>"] + self.left_wds
        self.left_labels = [tok.label for tok in lconx]
        self.right_wds = [tok.string for tok in rconx]
        if len(self.right_wds) < win:
            self.right_wds += ["</s>"] 
        self.lex_left_tags = {}
        self.lex_right_tags = {}
        if self.lex_dict:
            self.lex_left_tags = ["|".join(list(self.lex_dict.get(tok.string,{"unk":1}).keys()))
                                  for tok in lconx if tok is not None]
            self.lex_right_tags = ["|".join(list(self.lex_dict.get(tok.string,{"unk":1}).keys()))
                                   for tok in rconx if tok is not None]
        if self.tag_dict:
            self.train_left_tags = ["|".join(list(self.tag_dict.get(tok.string,{"unk":1}).keys()))
                                    for tok in lconx if tok is not None]
            self.train_right_tags = ["|".join(list(self.tag_dict.get(tok.string,{"unk":1}).keys()))
                                    for tok in rconx if tok is not None]
        return


    def add(self,name,key,value=-1):
        f = '%s=%s=%s' %(name,key,value)
        self.fv.append( f )
        return f


    def add_cached_feats(self,features):
        self.fv.extend(features)
        return


    def __str__(self):                                                     
        return '%s\t%s' %(self.label," ".join(self.fv))
    def weighted_str(self,w):
        return '%s $$$WEIGHT %f\t%s' %(self.label,w," ".join(self.fv))

    def get_features(self):
        self.get_static_features()
        self.get_sequential_features()
        return
    

    def get_sequential_features(self):
        ''' features based on preceding tagging decisions '''
        prev_labels = self.left_labels
        for n in range(1,self.context_window+1):
            if len(prev_labels) >= n:
                # unigram for each position
                if n == 1:
                    unigram = prev_labels[-n]
                else:
                    unigram = prev_labels[-n:-n+1][0]
                self.add('ptag-%s' %n, unigram)
                if n > 1:
                    # ngrams where 1 < n < window 
                    ngram = prev_labels[:n]
                    self.add('ptagS-%s' %n, "#".join(ngram))
        return


    def get_static_features(self):
        ''' features that can be computed independently from previous
        decisions'''
        self.get_word_features()
        self.get_conx_features()
        if self.lex_dict:
            self.add_lexicon_features()
        # NOTE: features for tag dict currently turned off
        # if self.tag_dict: 
        #     self.add_tag_dict_features()
        return


    def get_word_features(self, ln=5):
        ''' features computed based on word form: word form itself,
        prefix/suffix-es of length ln: 0 < n < 5, and certain regex
        patterns'''
        word = self.word
        index = self.index
        dico = self.lex_dict
        lex_tags = dico.get(word,{})
        # selecting the suffix confidence class for the word
        val = 1;
        if len(lex_tags) == 1:
            val = list(lex_tags.values())[0]
        else:
            val = 1
            for v in list(lex_tags.values()):
                if v == "0":
                    val = 0
                    break
        # word string-based features
        if word in self.cache:
            # if wd has been seen, use cache
            self.add_cached_features(self.cache[word])
        else:
            # word string
            self.add('wd',word)
            # suffix/prefix
            wd_ln = len(word)
            for i in range(1,ln):
                if wd_ln >= i:
                    self.add('pref%i' %i, word[:i])
                    self.add('suff%i' %i, word[-i:], val)
        # regex-based features
        self.add( 'nb', number.search(word) != None )
        self.add( 'hyph', hyphen.search(word) != None )
#        self.add( 'eq', equals.search(word) != None )
        uc = upper.search(word)
        self.add( 'uc', uc != None)
        self.add( 'niuc', uc != None and index > 0)
        self.add( 'auc', allcaps.match(word) != None)
        return



    def get_conx_features(self):
        ''' ngrams word forms in left and right contexts '''
        win = self.context_window
        lwds = self.left_wds
        rwds = self.right_wds
        # left/right contexts: ONLY UNIGRAMS FOR NOW
        for n in range(1,win+1):
            # LHS
            if len(lwds) >= n:
                # unigram
                if n == 1:
                    left_unigram = lwds[-n] 
                else:
                    left_unigram = lwds[-n:-n+1][0]
                self.add('wd-%s' %n, left_unigram)
                # ngram
                # if n > 1:
                #    left_ngram = lwds[-n:]
                #    self.add('wdS-%s' %n, "#".join(left_ngram))
            # RHS
            if len(rwds) >= n:
                # unigram
                right_unigram = rwds[n-1:n][0]
                self.add('wd+%s' %n, right_unigram)
                # ngram
                # if n > 1:
                #    right_ngram = rwds[:n]
                #    self.add('wdS+%s' %n, "#".join(right_ngram))
        # surronding contexts
        # if win % 2 == 0:
        #     win /= 2
        #     for n in range(1,win+1):
        #         surr_ngram = lwds[-n:] + rwds[:n]
        #         if len(surr_ngram) == 2*n:
        #             self.add('surr_wds-%s' %n, "#".join(surr_ngram))

        return



    def _add_lex_features(self, dico, ltags, rtags, feat_suffix): # for lex name
        lex_wd_feats = self.feat_selection.get('lex_wd',0)
        lex_lhs_feats = self.feat_selection.get('lex_lhs',0)
        lex_rhs_feats = self.feat_selection.get('lex_rhs',0)
        if lex_wd_feats:
            # ------------------------------------------------------------
            # current word
            # ------------------------------------------------------------
            word = self.word
            lex_tags = dico.get(word,{})
            if not lex_tags and self.index == 0:
                # try lc'ed version for sent initial words
                lex_tags = dico.get(word.lower(),{})
            if len(lex_tags) == 0:
                self.add('%s' %feat_suffix, "unk")
            elif len(lex_tags) == 1:
                # unique tag
                t = list(lex_tags.keys())[0]
                self.add('%s-u' %feat_suffix,t,lex_tags[t])
            else:
                # disjunctive tag
                self.add('%s-disj' %feat_suffix,"|".join(lex_tags))
                # individual tags in disjunction
                for t in lex_tags:
                    self.add('%s-in' %feat_suffix,t)
                    f = '%s=%s:%s' %(feat_suffix,t,lex_tags[t])

        # left and right contexts
        win = self.context_window
        for n in range(1,win+1):
            # ------------------------------------------------------------
            # LHS
            # ------------------------------------------------------------
            if lex_lhs_feats:
                if len(ltags) >= n:
                    # unigram
                    if n == 1:
                        left_unigram = ltags[-n]
                    else:
                        left_unigram = ltags[-n:-n+1][0]
                    self.add('%s-%s' %(feat_suffix,n), left_unigram)
                    # ngram
                    if n > 1:
                        left_ngram = ltags[-n:]
                        self.add('%sS-%s' %(feat_suffix,n), "#".join(left_ngram))
            # ------------------------------------------------------------
            # RHS
            # ------------------------------------------------------------
            if lex_rhs_feats:
                if len(rtags) >= n:
                    # unigram
                    right_unigram = rtags[n-1:n][0]
                    self.add('%s+%s' %(feat_suffix,n), right_unigram)
                    # ngram
                    if n > 1:
                        right_ngram = rtags[:n]
                        self.add('%sS+%s' %(feat_suffix,n), "#".join(right_ngram))
                        
        # surronding contexts
        
        if lex_lhs_feats and lex_rhs_feats:
            if win % 2 == 0:
                win //= 2
                for n in range(1,win+1):
                    surr_ngram = ltags[-n:] + rtags[:n]
                    if len(surr_ngram) == 2*n:
                        self.add('%s-surr-%s' %(feat_suffix,n), "#".join(surr_ngram))        
        return


    def add_lexicon_features(self):
        lex = self.lex_dict
        l_tags = self.lex_left_tags
        r_tags = self.lex_right_tags
        self._add_lex_features( lex, l_tags, r_tags, feat_suffix='lex')
        return


    def add_tag_dict_features(self):
        lex = self.tag_dict
        l_tags = self.train_left_tags
        r_tags = self.train_right_tags
        self._add_lex_features( lex, l_tags, r_tags, feat_suffix='tdict' )
        return

############################ utils.py ############################

def debug_n_best_sequence(n_best_sequences):
    print("debug")
    print(("\n".join([ "%s/%.2f" % (" ".join([str(t) for t in l]),s)  for l,s in n_best_sequences])).encode("utf8"))
    print("----")

def tag_dict(file_path):
    tag_dict = defaultdict(dict)
    for s in BrownReader(file_path,encoding="utf-8"):
        for wd,tag in s:
            tag_dict[wd][tag] = 1
    return tag_dict



def word_list(file_path,t=5):
    word_ct = {}
    for s in BrownReader(file_path,encoding="utf-8"):
        for wd,tag in s:
            word_ct[wd] =  word_ct.get(wd,0) + 1
    filtered_wd_list = {} 
    for w in word_ct:
        ct = word_ct[w]
        if ct >= t:
            filtered_wd_list[w] = ct
    return filtered_wd_list



def unserialize(filepath, encoding="utf-8"):
    _file = codecs.open( filepath, 'r', encoding=encoding )
    datastruct = loads( _file.read() )
    _file.close()
    return datastruct



def serialize(datastruct, filepath, encoding="utf-8"):
    _file = codecs.open( filepath, 'w', encoding=encoding )
    _file.write( dumps( datastruct ) )
    _file.close()
    return 

def filter_tokens(tokens,i):
    '''retourne la liste de token privée de ceux avant le i-eme et avec le i-eme en premier'''
    tok = tokens[i]
    result = [x for x in tokens if x.position[0] > tok.position[0]]
    return [tok] + result

def suivants_in_dag(tokens,i):
    if i is None :
        fin = 0
        i = -1
    else :
        fin = tokens[i].position[1]
    suivants = []
    for tok in tokens[i+1:len(tokens)]:
        if tok.position[0] == fin :
           suivants.append(tok)
    return suivants

def where_is_exec(program):
    ''' retourne le chemin d'un executable si il est trouvé dans le PATH'''
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


# ############## create tagger ##################################
# pos_tagger = POSTagger()

# # read-in tag dictionary from file
# if options.tag_dict:
#     pos_tagger.load_tag_dictionary( options.tag_dict )
# else:
#     print >> sys.stderr, "Warning: No tag dictionary provided"
    
# # read-in Lexicon
# if options.lexicon:
#     pos_tagger.load_lexicon( options.lexicon )
# else:
#     print >> sys.stderr, "Warning: External lexicon not provided"
    
# # induce/load model
# if options.train:
#     # make sure model directory exists, if not create it
#     if not os.path.isdir(options.model):
#         os.makedirs(options.model)
#     pos_tagger.train_model( options.train,
#                             model_path=options.model,
#                             prior_prec=options.prior_prec,
#                             repeat=options.repeat,
#                             maxit=options.maxit,
#                             classifier=options.classifier,
#                             feat_options=feat_select_options,
#                             dump_raw_model=options.dump_raw_model,
#                             dump_training_data=options.dump_training_data,
#                             zh_mode=options.ZH)
# elif options.model:
#     pos_tagger.load_model( options.model )
# else:
#     sys.exit("Error: please provide model file (-m) or training file (-t)")


# ############## apply tagger ##################################
# if options.gold_file or not options.train:
#     pos_tagger.apply( infile,
#                       outfile,
#                       handle_comments=options.handle_comments,
#                       print_probas=options.print_probas,
#                       lowerCaseCapOnly=options.lowercase_uppercase_sentences,
#                       beam_size=options.beam_size,
#                       feat_options=feat_select_options,
#                       zh_mode=options.ZH)


# ############## file closing ##################################
# infile.close()
# outfile.close()

# ############### eval ##################################
# #if options.gold_file and options.output_file:
# #    sink = AccuracySink()
# #    compare_files( options.gold_file, options.output_file, sink )
# #    print "\n>> OVERALL ACC: %s (%s/%s)" %(sink.score(),sink.correct,sink.total)

