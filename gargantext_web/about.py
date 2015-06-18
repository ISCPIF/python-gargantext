# -*- coding: utf-8 -*-

# Order in script: Alphabetical order (first_name, name, mail, website)
# Order in public: Shuffled order

import random

def get_team():
    '''
    Function to get list of each member as dict of personal informations.

    You are free to fill the form which is verbose indeed but clear enough for
    manual entries (I could zip lists but not clear enough).

    For your picture, please ask Alexandre to take your picture with his camera
    in order to follow the design shape of the website.

    '''
    team = [
            { 'first_name' : 'Alexandre', 'last_name' : 'Delanoë',
             'mail' : 'alexandre+gargantextATdelanoe.org',
             'website' : 'http://alexandre.delanoe.org',
             'picture' : 'alexandre.jpg',
             'role' : 'principal investigator, developer'},

            { 'first_name' : 'David', 'last_name' : 'Chavalarias',
             'mail' : 'david.chavalariasATiscpif.fr',
             'website' : 'http://chavalarias.com',
             'picture' : 'david.jpg',
             'role':'principal investigator'},

            { 'first_name' : 'Elias', 'last_name' : 'Showk',
             'mail' : '',
             'website' : 'https://github.com/elishowk',
             'picture' : '', 'role' : 'developer'},

            { 'first_name' : 'Mathieu', 'last_name' : 'Rodic',
             'mail' : '',
             'website'  : 'http://rodic.fr',
             'picture' : 'mathieu.jpg',
             'role' : 'developer'},

            { 'first_name' : 'Samuel', 'last_name' : 'Castillo J.',
             'mail' : 'kaisleanATgmail.com',
             'website'  : 'http://www.pksm3.droppages.com',
             'picture' : 'samuel.jpg',
             'role' : 'developer'},

            #{ 'first_name' : '', 'name' : '', 'mail' : '', 'website' : '', 'picture' : ''},
            # copy paste the line above and write your informations please
            ]

    random.shuffle(team)
    return(team)

def get_sponsors():
    '''
    Function to get list of each sponsor as dict of institutional informations.

    '''
    sponsors = [
            { 'name' : 'Mines ParisTech', 'website' : 'http://mines-paristech.fr', 'picture' : 'mines.png', 'funds':''},
            { 'name' : 'Institut Pasteur', 'website' : 'http://www.pasteur.fr', 'picture' : 'pasteur.png', 'funds':''},
            { 'name' : 'Forccast', 'website' : 'http://forccast.hypotheses.org/', 'picture' : 'forccast.png', 'funds':''},
            { 'name' : 'ADEME', 'website' : 'http://www.ademe.fr', 'picture' : 'ademe.png', 'funds':''},
            { 'name' : 'EHESS', 'website' : 'http://www.ehess.fr', 'picture' : 'ehess.png', 'funds':''},
            #{ 'name' : '', 'website' : '', 'picture' : '', 'funds':''},
            # copy paste the line above and write your informations please
            ]

    random.shuffle(sponsors)
    return(sponsors)

