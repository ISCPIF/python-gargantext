from node.models import Node, NodeType, Node_Resource,\
        Project, Corpus, Document,\
        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram,\
        User, Language, ResourceType, Resource

from math import log



# - tfidf / corpus , type de corpus, tous corpus
# - tfidf / échelle de temps
# - tfidf / sources, auteurs etc.
# => liste de listes



def tfidf(corpus, document, ngram):
    try:
        x = Node_Ngram.objects.get(node=document, ngram=ngram).weight
        y = Node_Ngram.objects.filter(node=document).count()
        tf = x/y
    
        xx = Node.objects.filter(parent=corpus, type=NodeType.objects.get(name="Document")).count()
        yy = Node_Ngram.objects.filter(ngram=ngram).count()
        idf= log(xx/yy)
        
        result = tf * idf
    except Exception as error:
        print(error)
        result = 0
    return result



def do_tfidf(corpus, reset=True):

    with transaction.atomic():
        if reset==True:
            NodeNodeNgram.objects.filter(nodex=corpus).delete()
        
        if isinstance(corpus, Node) and corpus.type.name == "Corpus":
            for document in Node.objects.filter(parent=corpus, type=NodeType.objects.get(name="Document")):
                for node_ngram in Node_Ngram.objects.filter(node=document):
                    try:
                        nnn = NodeNodeNgram.objects.get(nodex=corpus, nodey=document, ngram=node_ngram.ngram)
                    except:
                        score = tfidf(corpus, document, node_ngram.ngram)
                        nnn = NodeNodeNgram(nodex=corpus, nodey=node_ngram.node, ngram=node_ngram.ngram, score=score)
                        nnn.save()
        else:
            print("Only implemented for corpus yet, whereas you put:", type(corpus))



