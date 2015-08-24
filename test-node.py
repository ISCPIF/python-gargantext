# we have to set this before using Django's environment
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext_web.settings")
os.environ.setdefault("DJANGO_HSTORE_GLOBAL_REGISTER", "False")

# get the other kind of node
from gargantext_web.db import Session, Base, Node, NodeNgram, Ngram
# from node.Node import Session, Node

# test!
if __name__ == '__main__':

    step = 2
    session = Session()

    # nodes creation
    if step == 0:

        root = Node(nodetype='U', user_id=1, depth=0, lft=0, rgt=1, name='My stuff')
        session.add(root)
        session.commit()

        corpus = Node(nodetype='C', name='Super corpus')


        abstract = """The Radical Party was a proposed new political party in New Zealand. It was part of an abortive attempt by members of the Liberal Party to establish a breakaway group. No actual party was ever formed, but the name was frequently applied to the group of dissident MPs by the press.

            The leaders of the Radical Party proposal were George Russell and Frederick Pirani, both Liberal Party MPs. Russell and Pirani, along with other MPs such as William Collins and George Smith, were dissatisfied with the Liberal Party under Richard Seddon, believing that it had lost its commitment to its founding ideals. Both were considered to belong to the Liberal Party's left wing. In 1896, Russell spoke openly about formalising "the advanced section of the Liberal Party", either as an organised faction in the Liberal caucus or as a separate party.

            However, the new group failed to emerge. Tensions appeared to rise between its various members, with rumours circulating that neither Russell nor Pirani would concede the leadership to the other. The MPs whose names had been mentioned in connection with the Radical Party distanced themselves from it, stating that they had never made any commitments. Pirani and Smith both left the Liberal Party the same year, becoming independents.

            In 1905 a similar group, the New Liberal Party was formed, but this group was defunct by 1908.

            \f

            Mayahuel (Nahuatl pronunciation: [maˈjawel]) is the female divinity associated with the maguey plant among cultures of central Mexico in the Postclassic era of pre-Columbian Mesoamerican chronology, and in particular of the Aztec cultures. As the personification of the maguey plant, Mayahuel was also part of a complex of interrelated maternal and fertility goddesses in Aztec mythology and is also connected with notions of fecundity and nourishment.

            Products extracted from the maguey plant (Agave spp.) were used extensively across highlands and southeastern Mesoamerica, with the thorns used in ritual bloodletting ceremonies and fibers extracted from the leaves worked into ropes and cloth. Perhaps the most important maguey product is the alcoholic beverage known as pulque, used prominently in many public ceremonies and on other ritual occasions. By extension, Mayahuel is often shown in contexts associated with pulque. Although some secondary sources describe her as a "pulque goddess", she remains most strongly associated with the plant as the source, rather than pulque as the end product.

            Mayahuel has many breasts to feed her many children, the Centzon Totochtin (the 400 Rabbits). These are thought to be responsible for causing drunkenness.
            """
        document = Node(nodetype='D', depth=0)
        document.parse({'abstract': abstract, 'author': '.wikipedia'})

        corpus.append(document)
        root.append(corpus)
        print(root)
    
    # ngrams extraction
    elif step == 1:
        root = session.query(Node).filter(Node.depth == 0).first()
        root.extract_ngrams('abstract')
        # root.extract_ngrams('author')
        # root.extract_ngrams()

    # ngrams verification
    elif step == 2:
        root = session.query(Node).filter(Node.depth == 0).first()
        for ngram_terms, ngram_weight in root.fetch_descendants_ngrams():
            print(ngram_weight, ngram_terms)

