
import random
import random_words
from math import pi



def paragraph_lorem(size_target=450):
    '''
    Function that returns paragraph with false latin language.
    size_target is the number of random words that will be given.
    '''

    lorem = random_words.LoremIpsum()

    sentences_list = lorem.get_sentences_list(sentences=5)
    paragraph_size = 0

    while paragraph_size < size_target :
        sentences_list.append(lorem.get_sentence())
        paragraph = ' '.join(sentences_list)
        paragraph_size = len(paragraph)

    return(paragraph)


def paragraph_gargantua(size_target=500):
    '''
    Function that returns paragraph with chapter titles of Gargantua.
    size_target is the number of random words that will be given.
    '''

    paragraph = list()
    paragraph_size = 0
    chapter_number = 1

    while paragraph_size < size_target and chapter_number < 6:
        chapitre = open('/srv/gargantext/static/docs/gargantua_book/gargantua_chapter_' + str(chapter_number) + '.txt', 'r')
        paragraph.append(random.choice(chapitre.readlines()).strip())
        chapitre.close()
        paragraph_size = len(' '.join(paragraph))
        chapter_number += 1

    return(' '.join(paragraph))


def random_letter(mot, size_min=5):
    '''

    Functions that randomize order letters of a
    word which size is greater that size_min.

    '''
    if len(mot) > size_min:

        size = round(len(mot) / pi)

        first_letters = mot[:size]
        last_letters  = mot[-size:]

        others_letters = list(mot[size:-size])
        random.shuffle(others_letters)

        mot_list = list()
        mot_list.append(first_letters)

        for letter in others_letters:
            mot_list.append(letter)

        mot_list.append(last_letters)

        return(''.join(mot_list))

    else:
        return(mot)


tutoriel = """Il paraît que l'ordre des lettres dans un mot n'a pas d'importance. La première et la dernière lettre doivent être à la bonne place. Le reste peut être dans un désordre total et on peut toujours lire sans problème. On ne lit donc pas chaque lettre en elle-même, mais le mot comme un tout. Un changement de référentiel et nous transposons ce résultat au texte lui-même: l'ordre des mots est faiblement important comparé au contexte du texte qui, lui, est compté"""


def paragraph_tutoreil(tutoriel=tutoriel):
    '''
    Functions that returns paragraph of words with words with
    randomized letters.
    '''
    paragraph = ' '.join([ random_letter(mot) for mot in tutoriel.split(" ")]) \
            + ": comptexter avec Gargantext."
    return(paragraph)
