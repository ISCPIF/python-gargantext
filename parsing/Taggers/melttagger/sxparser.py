#!/usr/bin/env python
# -*- coding:utf8 -*-

from .ply import yacc as sxyacc

from . import sxlexer
import sys
tokens = sxlexer.tokens
from collections import defaultdict as dd

precedence = (
    ('left','WORD'),
    ('left','_','|'),
)



class Token():
    def __init__(self,form,pos="UNK",sem=None,com=None):
        self.forme = form
        self.semantique = sem
        self.commentaire = com
        self.pos = pos
    def to_string(self):
        acc = ""
        if self.commentaire:
            acc += "{%s} " % (self.commentaire,)
        acc += "%s__%s " % (self.forme,self.pos)
        if self.semantique:
            acc += "[|%s|] " % (self.semantique,)
        return acc
        
class TokenSequence():
    def __init__(self,seq=[]):
        self.seq = seq
    def append(self,elem):
        if isinstance(elem,Token):
            self.seq.append(elem)
        if isinstance(elem,TokenSequence):
            self.seq.extend(elem.seq)
        if isinstance(elem,TokenDisjunction):
            self.seq.append(elem)
    def to_string(self):
        return " ".join([t.to_string() for t in self.seq])
        
class TokenDisjunction():
    def __init__(self,options=[]):
        self.options = options
    def append(self,elem):
        if isinstance(elem,Token):
            self.options.append(TokenSequence([elem]))
        if isinstance(elem,TokenSequence):
            self.options.append(elem)
        if isinstance(elem,TokenDisjunction):
            self.options.extend(elem.options)
    def to_string(self):
        return "( %s )" % ("|".join([seq.to_string() for seq in self.options]),)
        
def p_error(p):
    print("Syntax error at '%s'" % p.value)
    sys.exit(1)


def p_tokseq(p):
    '''tokseq : tokseq token
              | tokseq disjonction
              | disjonction
              | token'''
    if len(p) < 3 :
        p[0] = TokenSequence([p[1]])
    else :
        p[1].append(p[2])
        p[0] = p[1] 
    #p[0] = ("TokSeq", p[1][1] + [p[2]],p[1][2] + p[2][2] ) if len(p)>2 else ("TokSeq",[p[1]],p[1][2])

def p_disjonction(p):
    ''' disjonction : '(' disjseq ')' '''
    p[0] = p[2]

def p_disjseq(p):
    ''' disjseq : disjseq '|' tokseq
                | tokseq'''
    if len(p) < 3 :
        p[0] = TokenDisjunction([p[1]])
    else :
        p[1].append(p[3])
        p[0] = p[1]
    #p[0] = ('OR',p[1][1] + [p[3]],max(p[1][2] ,p[3][2])) if len(p)>2 else ('OR', [p[1]],p[1][2])


def p_token(p):
    ''' token : commentaire formepos sem 
              | commentaire formepos
              | formepos sem
              | formepos'''
    feats = p[1][1]
    if len(p)>2:
        for d in p[2:]:
            feats.update(d[1])
    for f in ["Com","Sem"]:
        feats[f] = " ".join(feats[f]) if f in feats else None
    p[0] = Token(feats["Forme"], feats["POS"], feats["Sem"], feats["Com"])
    #p[0] = ("Tok",feats,1)



def p_commentaire(p) :
    ''' commentaire : '{' wordlist '}' '''
    p[0] = ("Com",{"Com": p[2][1]})

def p_sem(p):
    ''' sem : SEM_G wordlist SEM_D '''
    p[0] = ("Sem",{"Sem": p[2][1]})

def p_formepos(p):
    '''formepos : special_char
                | normal_token
                | no_pos '''
    p[0] = p[1]
    
def p_normal_token(p):
    '''normal_token : no_pos '_' '_' WORD '''
    p[0] = ('Forme',{"Forme":p[1][1]["Forme"], "POS":p[4]})


def p_no_pos(p):
    ''' no_pos : WORD '''
    p[0] = ('Forme',{"Forme":p[1], "POS":""})

def p_special_char(p):
    '''special_char : '_' WORD
                    | '_' WORD '_' WORD'''
    p[0] = ('Forme',{"Forme": "".join(p[1:]), "POS":"escaped"})

def p_wordlist(p):
    '''wordlist : wordlist WORD
                | WORD'''
    if len(p)>2 :
        p[0] = ('WL',p[1][1] + [p[2]])
    else :
        p[0] = ('WL',[p[1]])
    
    
    
sxyacc.yacc(debug=0,write_tables=0)

data =  ' {debut} A_1 ( B_2 [|s|] {com} C_2 | D_3 ( E_4 | F_5 ) G_12 | H_15 I_1 J_2 | K_1  ) {fin} Z_4 '

def list_of_dag(dag,debut=0,fin = -1,acc = []):
    if dag[0] == "TokSeq" :
        for elem in dag[1][:-1] :
            acc = list_of_dag(elem,debut,fin=-1,acc=acc)
            debut += elem[2]
        last = dag[1][-1]
        acc = list_of_dag(last,debut,fin,acc)
    elif dag[0] == "OR" :
        fin = debut + dag[2]
        for seq in dag[1] :
            acc = list_of_dag(seq,debut,fin,acc)
    elif dag[0] == "Tok":
        if fin == -1 :
            fin = debut + dag[2]
        acc.append((debut,fin,dag))
    elif dag[0] == "Word":
        if fin == -1 :
            fin = debut + len(dag[1]["Forme"])
        acc.append((debut,fin,dag))
    return acc
    
    
    
def prefix_commun(tokseqA,tokseqB):
    '''cherche un prefixe commun et retourne un triplet (prefixe,tokseqA',tokseqB')
        où tokseqX' correspond à tokseqA sans le prefixe'''
    lpref = 0
    pref = TokenSequence([])
    #tokseqA = flatten(tokseqA)
    #tokseqB = flatten(tokseqB)
    i = 0
    while len(tokseqA[1]) > i and len(tokseqB[1]) > i :
        toka = tokseqA.seq[i]
        tokb = tokseqB.seq[i]
        if tokb == toka :
            pref.append(tokb)
            #tokseqA.seq.pop(0)
            #tokseqB.seq.pop(0)
            lpref += 1
            i += 1
        else :
            break
    if lpref == 0 :
        return (None,tokseqA,tokseqB)
    tokseqA2 = TokenSequence(tokseqA.seq[i:])
    tokseqB2 = TokenSequence(tokseqB.seq[i:])
    return ( pref, tokseqA2, tokseqB2 )
        
        

def dag_of_list(l):
    ''' l : liste de tokens et mots au format (debut,fin,('Tok',feat,length))
        les couples (debut,fin) sont supposés uniques 
        (cad il existe une et une seule transition entre deux états)
        retourne une sortie semblable au parse d'un format sxpipe'''
    l = list(l)
    etats = set()
    for t in l :
        etats.add(t[1])
        
    final = max(etats)
    etats.remove(final)
    for i in sorted(list(etats)):
        precs = [x for x in l if x[1] == i]
        suivs = [x for x in l if x[0] == i]
        for p in precs :
            for s in suivs :
                new = (p[0],s[1],("TokSeq",[p[2],s[2]],p[2][2]+s[2][2]))
                ps = [x for x in l if x[0] == p[0] and x[1] == s[1]]
                if len(ps) == 1 :
                    #assert(ps[0][2][0] == "TokSeq")
                    pref = None
                    if p[2][0] == "TokSeq" and ps[0][2][0] == "TokSeq" :
                        (pref,seqa,seqb) = prefix_commun(p[2],ps[0][2])
                    
                    if pref :
                        newSq = ("TokSeq",[seqa,s[2]],seqa[2]+s[2][2])
                        new = (p[0],s[1],("TokSeq",[pref,("OR",[newSq,seqb],seqb[2])],ps[0][2][2]))
                    else :
                        newSq = ("TokSeq",[p[2],s[2]],p[2][2]+s[2][2])
                        new = (p[0],s[1],("OR",[ps[0][2],newSq],ps[0][2][2]))
                    l.remove(ps[0])
                else :
                    #?!?!?!
                    newSq = ("TokSeq",[p[2],s[2]],p[2][2]+s[2][2])
                    new = (p[0],s[1],newSq)
                l.remove(s)
                l.append(new)
            l.remove(p)
    #return flatten(l[0][2]) 
    
    
def dag_of_fsa(l):
    ''' liste : l de tokens et mots au format (debut,fin,('Tok',feat,length))
        les couples (debut,fin) sont supposés uniques 
        (cad il existe une et une seule transition entre deux états)
        retourne une sortie semblable au parse d'un format sxpipe'''
    l = list(l)
    etats = set()
    for t in l :
        etats.add(t[1])
    final = max(etats)
    etats.remove(final)
    for i in sorted(list(etats)):
        precs = [x for x in l if x[1] == i]
        suivs = [x for x in l if x[0] == i]
        for p in precs :
            for s in suivs :
                
                new_ts = TokenSequence([])
                new_ts.append(p[2])
                new_ts.append(s[2])
                new = (p[0],s[1],new_ts)
                ps = [x for x in l if x[0] == p[0] and x[1] == s[1]]
                if len(ps) >= 1 :
                    new_td = TokenDisjunction([])
                    new_td.append(new_ts)
                    for alt in ps :
                        new_td.append(alt[2])
                        l.remove(alt)
                    new = (p[0],s[1],new_td)
                l.remove(s)
                l.append(new)
            l.remove(p)
    #faudrait flattener
    return l[0][2]

#def concat(l):
#    return ("TokSeq",l,sum([x[2] for x in l]))

escape_chart = [("_"," _UNDERSCORE "),\
                ("|"," _PIPE "),\
                ("{"," _O_BRACE "),\
                ("}"," _C_BRACE "),\
                ("["," _O_BRACKET "),\
                ("]"," _C_BRACKET "),\
                ("(","_O_PAR"),\
                (")","_C_PAR")]


def escape(s):
    for (a,b) in escape_chart :
        s = s.replace(a,b)
    return s
    #return s.replace("_"," _UNDERSCORE ").replace("|"," _PIPE ").replace("{"," _O_BRACE ").replace("}"," _C_BRACE ").replace("["," _O_BRACKET ").replace("]"," _C_BRACKET ").replace("(","_O_PAR").replace(")","_C_PAR")

def unescape(s):
    for (a,b) in reversed(escape_chart):
        s = s.replace(b,a)
    return s

#def to_string(dag):
#    acc = ""
#    if dag[0] == "TokSeq" :
#        for t in dag[1] :
#            acc += to_string(t)
#    elif dag[0] == "OR" :
#        acc += "( "
#        for t in dag[1][:-1] :
#            acc += to_string(t)
#            acc += "| "
#        acc += to_string(dag[1][-1]) + ") "
#    else :
#        f = dag[1]
#        if f["Com"] != "":
#            acc += "{%s} " % (f["Com"],)
#        acc += "%s_%s " % (f["Forme"],f["POS"])
#        if f["Sem"] != "":
#            acc += "[|%s|] " % (f["Sem"],)
#        
#    return acc

#TODO:
#def saucissonne_dage(dag):

def fsa_of_dag(dag):
    def fsaify_sequence(tokseq,debut,suiv,states):
        for tok in tokseq.seq:
            if isinstance(tok,Token):
                states.append((debut,suiv,tok))
                debut = suiv
                suiv += 1
            if isinstance(tok,TokenDisjunction):
                suiv = fsaify_disjunction(tok,debut,suiv,states)
                debut = suiv
                suiv += 1
        return suiv
    def fsaify_disjunction(tokdisj, debut, suiv, states):
        for tok in tokdisj.options :
            if isinstance(tok,Token):
                states.append((debut,None,tok))
                suiv += 1
            if isinstance(tok,TokenDisjunction):
                assert(False)
                suiv = fsaify_disjunction(tok,debut,suiv,states)
            if isinstance(tok,TokenSequence):
                suiv = fsaify_sequence(tok,debut,suiv,states)
                suiv -= 1
                for i in range(len(states)):
                    if states[i][1] == suiv:
                        states[i] = (states[i][0],None,states[i][2])
        for i in range(len(states)):
            if states[i][1] == None:
                states[i] = (states[i][0], suiv, states[i][2])
        return suiv
    if isinstance(dag,TokenSequence):
        states = []
        fsaify_sequence(dag,0,1,states)
        return states
    if isinstance(dag,TokenDisjunction):
        states = []
        fsaify_disjunction(dag,0,1,states)
        return states
    else :
        return [(0,1,dag)]
        
if __name__ == "__main__":
    data =  'tok__NP'
    print(sxyacc.parse(data).to_string())
    data =  'tok__NP tok2__VP'
    print(sxyacc.parse(data).to_string())
    data =  ' {debut} A__1 ( B__2 [|s|] {com} C__2 | D__3 ( E__4 | F__5 ) ) {fin} E__4 '
    print(sxyacc.parse(data).to_string())
    print("->fsa")
    print([(a,b,c.to_string()) for (a,b,c) in fsa_of_dag(sxyacc.parse(data))])
    print("->fsa->dag")
    print(dag_of_fsa(fsa_of_dag(sxyacc.parse(data))).to_string())

