
from collections import defaultdict

from django.db import connection
from documents.models import Document, Ngram, NgramTemporary, NgramDocumentTemporary

import nltk
from nltk.stem.snowball import EnglishStemmer

from analysis.languages import english_pos_tag
from analysis.languages import english_stem

#    if corpus.language == 'Français':
#        from analysis.languages import french_pos_tag as pos_tag
#        from analysis.languages import french_stem as stem
#        print("Selection langue anglaise")

stemmer = EnglishStemmer()

l = set()
# du format: terms, stems, count

d = defaultdict( lambda:\
    defaultdict( lambda:\
    defaultdict( lambda:\
    defaultdict( int )\
    )))

# if isinstance(corpus, Corpus) and field in [ column.name for column in Document._meta.fields]:

def save_newgrams(new_grams):
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




def words_field(corpus=None, field='abstract'):
    docs = Document.objects.filter(corpus=corpus)
    
    def ngrams(text, grammar_rule='jj_nn'):
        # TODO : grammar_rule
        from analysis.grammar_rules import jj_nn as rule
        grammar = nltk.RegexpParser(rule)

        #text = clean(text)
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

    def ograms(text, field=doc.abstract)
        try:
            sentences = nltk.sent_tokenize(field)
            words = [ nltk.wordpunct_tokenize(str(sentence)) for sentence in sentences ]

            for word in words[0]:
                try:
                    stems = stemmer.stem(str(word))
                    new = (word, stems, len(stems.split(" ")))
                    l.add(new)
    
                    d[word][doc.id]['count'] = d[word][doc.pk].get('count', 0) + 1
                except Exception as e: pass#print(e)
    
        except Exception as e: pass#print(e)
    

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
    

    new_grams   = [ Ngram(terms=x[0], stem=x[1], n=x[2]) for x in l]
    new_gramDoc = [ NgramDocumentTemporary(terms=k, document=pk, occurrences=d[k][pk]['count']) \
               for k in d.keys() \
               for pk in d[k].keys() ]

    save_newgrams(new_grams)

    
def words_fields(corpus=None, fields=['title',]):
    try:
        for field in fields:
            words_field(corpus=corpus, field=field)
    except Exception as e: print(e)


