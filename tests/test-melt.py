from parsing.Taggers import MeltTagger


texts = {
    'en':
        """Air raids on Japan by the Allies in World War II caused extensive destruction and casualties; the most commonly cited estimates are 333,000 killed and 473,000 wounded.
        During the first years of the Pacific War, these attacks were limited to the Doolittle Raid in April 1942 and small-scale raids on military positions in the Kuril Islands starting in mid-1943. Strategic bombing raids began in June 1944 and were greatly expanded in November. The raids initially attempted to target industrial facilities, but from March 1945 onwards were generally directed against urban areas. Aircraft flying from aircraft carriers and the Ryukyu Islands also frequently struck targets in Japan during 1945 in preparation for an Allied invasion planned for October. In early August, the cities of Hiroshima and Nagasaki were struck and mostly destroyed by atomic bombs. Japan's military and civil defenses were not capable of protecting the country, and the Allied forces generally suffered few losses. The bombing campaign was one of the main factors in the Japanese government's decision to surrender in mid-August 1945. Nevertheless, there has been a long-running debate over the attacks on Japanese cities, and the decision to use atomic weapons has been particularly controversial.
        """,
    'fr':
        """Le vieil hôtel de ville, construit de 1608 à 1610 est le plus ancien bâtiment de la ville de Wiesbaden. Il se dresse sur la place centrale de la vieille ville, la Place du Palais, qui abrite aujourd'hui le Parlement de l'État de Hesse, l'église et l'hôtel de ville.
        Il a été construit dans le style Renaissance. On a ajouté, en 1828, un étage de style romantique historié. Sur les bas-reliefs des cinq fenêtres de l'étage, en bois, étaient représentées les vertus de la force, la justice, la charité, de prudence et de modération, alors que la pierre a remplacé par des copies. Le pièces de chêne d'origine peut être visitées aujourd'hui au Musée de Wiesbaden. Aujourd'hui, le bâtiment sert de bureau de la ville de Wiesbaden.
        Devant le porche, entre l'hôtel de Ville et l'Ancien hôtel de ville, se trouve la colonne centrale de Nassau, un lion couronné avec bouclier.
        Il s'agit de construire progressivement, à partir des données initiales, un sous-graphe dans lequel sont classés les différents sommets par ordre croissant de leur distance minimale au sommet de départ. La distance correspond à la somme des poids des arêtes empruntées.
        Au départ, on considère que les distances de chaque sommet au sommet de départ sont infinies. Au cours de chaque itération, on va mettre à jour les distances des sommets reliés par un arc au dernier du sous-graphe (en ajoutant le poids de l'arc à la distance séparant ce dernier sommet du sommet de départ ; si la distance obtenue ainsi est supérieure à celle qui précédait, la distance n'est cependant pas modifiée). Après cette mise à jour, on examine l'ensemble des sommets qui ne font pas partie du sous-graphe, et on choisit celui dont la distance est minimale pour l'ajouter au sous-graphe.
        La première étape consiste à mettre de côté le sommet de départ et à lui attribuer une distance de 0. Les sommets qui lui sont adjacents sont mis à jour avec une valeur égale au poids de l'arc qui les relie au sommet de départ (ou à celui de poids le plus faible si plusieurs arcs les relient) et les autres sommets conservent leur distance infinie.
        Le plus proche des sommets adjacents est alors ajouté au sous-graphe.
        La seconde étape consiste à mettre à jour les distances des sommets adjacents à ce dernier. Encore une fois, on recherche alors le sommet doté de la distance la plus faible. Comme tous les sommets n'avaient plus une valeur infinie, il est donc possible que le sommet choisi ne soit pas un des derniers mis à jour.
        On l'ajoute au sous-graphe, puis on continue ainsi à partir du dernier sommet ajouté, jusqu'à épuisement des sommets ou jusqu'à sélection du sommet d'arrivée.
        """,
}

language = 'en'
text = texts[language]

if __name__ == '__main__':
    from time import time
    t0 = time()
    tagger = MeltTagger(language=language)
    print(time() - t0)
    print()
    i = 0
    t0 = time()
    for x in tagger.tag_text(text, lemmatize=True):
        print(x)
        i += 1
    t = time() - t0
    print(t)
    print(t / i)
