
from collections import defaultdict

from django.db import connection
from documents.models import Document, Ngram, NgramTemporary, NgramDocumentTemporary

import nltk
from nltk.stem.snowball import EnglishStemmer

stemmer = EnglishStemmer()


l = set()

d = defaultdict( lambda:\
    defaultdict( lambda:\
    defaultdict( lambda:\
    defaultdict( int )\
    )))

#if isinstance(corpus, Corpus) and field in [ column.name for column in Document._meta.fields]:

def words_field(corpus=None, field='abstract'):
    
    docs = Document.objects.filter(corpus=corpus)
    
    if corpus.language == 'Français':
        from .languages import french_pos_tag as pos_tag
        from .languages import french_stem as stem

    elif corpus.language == 'English':
        from .languages import english_pos_tag as pos_tag
        from .languages import english_stem as stem

    
    def fouille(text, grammar_rule='jj_nn'):
        # TODO: grammar_rule
        from .grammar_rules import jj_nn as rule
        grammar = nltk.RegexpParser(rule)
        
        text = clean(text)
        sentances = nltk.sent_tokenize(text)
        result = []
        
        for sentance in sentances:
            try:
                t = pos_tag(sentance)
                g = grammar.parse(t)
                x = g.subtrees()
            
                while True:
                    try:
                        subtree = next(x)
                        if subtree.label() == 'NP':
                            #print(subtree.label())
                            result.append(subtree.leaves())
                            
                    except Exception as e:
                        break
                        
            except Exception as e:
                print(e)
                pass
                
        return iter(result)

    if True:
    #if isinstance(corpus, Corpus):
        for doc in corpus:
            text = doc.get(key, '')
            u_id = doc.get(unique_id, 'XX')
            date = doc.get('date', 'XX')

            ngrams = fouille(text)
            
            while True:
                try:
                    leave = next(ngrams)
                    words = stems(leave)
                    s = words[0]
                    w  = tuple(words[1])

                    if s not in set(self.stems.keys()):
                        self.stems[s]['synonyms']                = set()
                        self.stems[s]['frequency'][date][u_id]   = 0
        # TODO c-value, nonograms and ngrams
                        
                        if w not in self.stems[s]['synonyms']:
                            self.stems[s]['synonyms'].add(w)
                        
                    self.stems[s]['frequency'][date][u_id] += 1
                
                except Exception as e:
                    #print('h',e)
                    break


    for doc in docs:
        try:
            sentences = nltk.sent_tokenize(doc.abstract)
            words = [ nltk.wordpunct_tokenize(str(sentence)) for sentence in sentences ]
    
            for word in words[0]:
                try:
                    stems = stemmer.stem(str(word))
                    new = (word, stems, len(stems.split(" ")))
                    l.add(new)
                    
                    d[word][doc.id]['count'] = d[word][doc.pk].get('count', 0) + 1
                except Exception as e: pass#print(e)
#             
        except Exception as e: pass#print(e)
#
    new_grams   = [ Ngram(terms=x[0], stem=x[1], n=x[2]) for x in l]
    new_gramDoc = [ NgramDocumentTemporary(terms=k, document=pk, occurrences=d[k][pk]['count']) \
               for k in d.keys() \
               for pk in d[k].keys()\
               ]

    NgramTemporary.objects.bulk_create(new_grams)
    NgramDocumentTemporary.objects.bulk_create(new_gramDoc)

    cursor = connection.cursor()
    # LOCK TABLE documents_ngramtemporary IN EXCLUSIVE MODE;
    query_string = """
                 INSERT INTO documents_ngram 
                 SELECT * FROM documents_ngramtemporary WHERE NOT EXISTS 
                 ( SELECT 1 FROM documents_ngram WHERE 
                 documents_ngram.terms = documents_ngramtemporary.terms);
                 
                 delete from documents_ngramtemporary;
                 
                 INSERT INTO 
                 documents_ngramdocument (terms_id, document_id, occurrences)
                 SELECT 
                 GT.id, DT.id, NDT.occurrences 
                 FROM 
                 documents_ngramdocumenttemporary as NDT 
                 INNER JOIN documents_document AS DT ON DT.id = NDT.document 
                 INNER JOIN documents_ngram AS GT ON GT.terms = NDT.terms ;
                 
                 delete from documents_ngramdocumenttemporary;
             """
    cursor.execute(query_string)


def words_fields(corpus=None, fields=['title',]):
    try:
        for field in fields:
            words_field(corpus=corpus, field=field)
    except Exception as e: print(e)


