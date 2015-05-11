#!/usr/bin/env python

from .ply import lex

tokens = [ 'WORD','SEM_G', 'SEM_D']
t_ignore = ' '
t_SEM_G = r'\[\|'
t_SEM_D = r'\|\]'
t_WORD = r'[^_{}[\]\|\(\) ]+'

def t_error(t):
    t.type = t.value[0]
    t.value = t.value[0]
    t.lexer.skip(1)
    return t

literals = '_{}|()'

lex.lex()

if __name__ == "__main__" :
    test = 'tok_NP {com} tok2_VP [|sem|]'
    lex.input(test)
    while True :
        t = lex.token()
        print(t)
        if not t :
            break
