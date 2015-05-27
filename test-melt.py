from parsing.Taggers import MeltTagger


# from parsing.Taggers.melttagger.tagger import POSTagger, Token, DAGParser, DAGReader


# # references:
# # - http://cs.nyu.edu/grishman/jet/guide/PennPOS.html
# # - http://www.lattice.cnrs.fr/sites/itellier/SEM.html
# class identity_dict(dict):
#     def __missing__(self, key):
#         return key
# _tag_replacements = identity_dict({
#     'DET':      'DT',
#     'NC':       'NN',
#     'NPP':      'NNP',
#     'ADJ':      'JJ',
#     'PONCT':    '.',
#     'ADVWH':    'WRB',
#     'ADV':      'RB',
#     'DETWH':    'WDT',
#     'PROWH':    'WP',
#     'ET':       'FW',
#     'VINF':     'VB',
#     'I':        'UH',
#     'CS':       'IN',

#     # 'CLS':      '',
#     # 'CLR':      '',
#     # 'CLO':      '',
    
#     # 'PRO':      '',
#     # 'PROREL':   '',
#     # 'P':        '',
#     # 'P+D':      '',
#     # 'P+PRO':    '',

#     # 'V':        '',
#     # 'VPR':      '',
#     # 'VPP':      '',
#     # 'VS':       '',
#     # 'VIMP':     '',

#     # 'PREF':     '',
#     # 'ADJWH':    '',
# })


# import subprocess


# class MeltTagger:

#     def __init__(self, language='fr', melt_data_path='./parsing/Taggers/melttagger'):
#         path = '%s/%s' % (melt_data_path, language)
#         self.pos_tagger = POSTagger()
#         self.pos_tagger.load_tag_dictionary('%s/tag_dict.json' % path)
#         self.pos_tagger.load_lexicon('%s/lexicon.json' % path)
#         self.pos_tagger.load_model('%s' % path)
#         self._preprocessing_commands = (
#             # ('/usr/local/bin/clean_noisy_characters.sh', ),
#             # ('/usr/local/bin/MElt_normalizer.pl', '-nc', '-c', '-d', '/usr/local/share/melt/normalization/%s' % language, '-l', language, ),
#             ('/usr/local/share/melt/segmenteur.pl', '-a', '-ca', '-af=/usr/local/share/melt/pctabr', '-p', 'r'),
#         )
#         self._lemmatization_commands = (
#             ('/usr/local/bin/MElt_postprocess.pl', '-npp', '-l', language),
#             ('MElt_lemmatizer.pl', '-m', '/usr/local/share/melt/%s' % language),
#         )

#     def pipe(self, text, commands, encoding='utf8'):
#         text = text.encode(encoding)
#         # print(text.decode(encoding))
#         for command in commands:
#             # print(command)
#             process = subprocess.Popen(
#                 command,
#                 bufsize=0,
#                 stdin=subprocess.PIPE,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#             )
#             text, err = process.communicate(text)
#             # print()
#             # print(text.decode(encoding))
#             if len(err):
#                 print(err.decode(encoding))
#         return text.decode(encoding)

#     def tag(self, text, encoding='utf8', lemmatize=True):
#         preprocessed = self.pipe(text, self._preprocessing_commands)
#         if lemmatize:
#             result = ''
#             for sentence in preprocessed.split('\n'):
#                 words = sentence.split(' ')
#                 tokens = [Token(word) for word in words]
#                 tagged_tokens = self.pos_tagger.tag_token_sequence(tokens)
#                 # result += ' '.join(token.__str__() for token in tagged_tokens)
#                 for token in tagged_tokens:
#                     if len(token.string):
#                         result += '%s/%s ' % (token.string, token.label, )
#                 result += '\n'
#             lemmatized = self.pipe(result, self._lemmatization_commands)
#             for sentence in lemmatized.split('\n'):
#                 for token in sentence.split(' '):
#                     if len(token):
#                         yield tuple(token.split('/'))
#         else:
#             for sentence in preprocessed.split('\n'):
#                 words = sentence.split(' ')
#                 tokens = [Token(word) for word in words]
#                 tagged_tokens = self.pos_tagger.tag_token_sequence(tokens)
#                 for token in tagged_tokens:
#                     if len(token.string):
#                         yield (token.string, _tag_replacements[token.label], )


if __name__ == '__main__':
    from time import time
    t0 = time()
    tagger = MeltTagger()
    print(time() - t0)
    print()
    text = """Le vieil hôtel de ville, construit de 1608 à 1610 est le plus ancien bâtiment de la ville de Wiesbaden. Il se dresse sur la place centrale de la vieille ville, la Place du Palais, qui abrite aujourd'hui le Parlement de l'État de Hesse, l'église et l'hôtel de ville.
        Il a été construit dans le style Renaissance. On a ajouté, en 1828, un étage de style romantique historié. Sur les bas-reliefs des cinq fenêtres de l'étage, en bois, étaient représentées les vertus de la force, la justice, la charité, de prudence et de modération, alors que la pierre a remplacé par des copies. Le pièces de chêne d'origine peut être visitées aujourd'hui au Musée de Wiesbaden. Aujourd'hui, le bâtiment sert de bureau de la ville de Wiesbaden.
        Devant le porche, entre l'hôtel de Ville et l'Ancien hôtel de ville, se trouve la colonne centrale de Nassau, un lion couronné avec bouclier.
        Il s'agit de construire progressivement, à partir des données initiales, un sous-graphe dans lequel sont classés les différents sommets par ordre croissant de leur distance minimale au sommet de départ. La distance correspond à la somme des poids des arêtes empruntées.
        Au départ, on considère que les distances de chaque sommet au sommet de départ sont infinies. Au cours de chaque itération, on va mettre à jour les distances des sommets reliés par un arc au dernier du sous-graphe (en ajoutant le poids de l'arc à la distance séparant ce dernier sommet du sommet de départ ; si la distance obtenue ainsi est supérieure à celle qui précédait, la distance n'est cependant pas modifiée). Après cette mise à jour, on examine l'ensemble des sommets qui ne font pas partie du sous-graphe, et on choisit celui dont la distance est minimale pour l'ajouter au sous-graphe.
        La première étape consiste à mettre de côté le sommet de départ et à lui attribuer une distance de 0. Les sommets qui lui sont adjacents sont mis à jour avec une valeur égale au poids de l'arc qui les relie au sommet de départ (ou à celui de poids le plus faible si plusieurs arcs les relient) et les autres sommets conservent leur distance infinie.
        Le plus proche des sommets adjacents est alors ajouté au sous-graphe.
        La seconde étape consiste à mettre à jour les distances des sommets adjacents à ce dernier. Encore une fois, on recherche alors le sommet doté de la distance la plus faible. Comme tous les sommets n'avaient plus une valeur infinie, il est donc possible que le sommet choisi ne soit pas un des derniers mis à jour.
        On l'ajoute au sous-graphe, puis on continue ainsi à partir du dernier sommet ajouté, jusqu'à épuisement des sommets ou jusqu'à sélection du sommet d'arrivée.
    """
    i = 0
    t0 = time()
    for x in tagger.tag_text(text, lemmatize=True):
        print(x)
        i += 1
    t = time() - t0
    print(t)
    print(t / i)
