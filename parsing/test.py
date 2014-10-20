from NgramsExtractors import *
from Taggers import *


texts = [
    "This is quite a simple test.",
    "Forman Brown (1901–1996) was one of the world's leaders in puppet theatre in his day, as well as an important early gay novelist. He was a member of the Yale Puppeteers and the driving force behind Turnabout Theatre. He was born in Otsego, Michigan, in 1901 and died in 1996, two days after his 95th birthday. Brown briefly taught at North Carolina State College, followed by an extensive tour of Europe.",
    "James Patrick (born c. 1940) is the pseudonym of a Scottish sociologist, which he used to publish a book A Glasgow Gang Observed. It attracted some attention in Scotland when it was published in 1973. It was based on research he had done in 1966, when he was aged 26. At that time he was working as a teacher in an Approved School, a Scottish reformatory. One gang member in the school, \"Tim Malloy\" (born 1950, also a pseudonym and a generic term for a Glasgow Catholic), agreed to infiltrate him into his gang in Maryhill in Glasgow. Patrick spent four months as a gang member, observing their behaviour.",
]
tagger = NltkTagger()
extractor = EnglishNgramsExtractor()

# texts = [
    # "La saison 1921-1922 du Foot-Ball Club Juventus est la vingtième de l'histoire du club, créé vingt-cinq ans plus tôt en 1897. La société turinoise qui fête cette année son 25e anniversaire prend part à l'édition du championnat dissident d'Italie de la CCI (appelé alors la Première division), la dernière édition d'une compétition annuelle de football avant l'ère fasciste de Mussolini.",
    # "Le terme oblong désigne une forme qui est plus longue que large et dont les angles sont arrondis. En langage bibliographique, oblong signifie un format dont la largeur excède la hauteur. Ce qui correspond au format paysage en termes informatiques et \"à l'italienne\", pour l'imprimerie.",
    # "Les sanglots longs des violons de l'automne bercent mon coeur d'une langueur monotone.",
# ]
# tagger = TreeTagger()
# extractor = FrenchNgramsExtractor()


for text in texts:
    print(tagger.tag_text(text))
    print()
    ngrams = extractor.extract_ngrams(text)
    for ngram in ngrams:
        print("\t" + str(ngram))
    print("\n")