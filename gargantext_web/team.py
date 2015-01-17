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
            { 'first_name' : 'Alexandre', 'name' : 'Delanoë', 'mail' : 'alexandre+gargantextATdelanoe.org', 'website' : 'http://alexandre.delanoe.org', 'picture' : 'alexandre.png'},
            { 'first_name' : 'David', 'name' : 'Chavalarias', 'mail' : '', 'website' : 'http://chavalarias.com', 'picture' : 'david.png'},
            { 'first_name' : 'Mathieu', 'name' : 'Rodic', 'mail' : '', 'website'  : 'http://rodic.fr', 'picture' : 'mathieu.png'},
            { 'first_name' : 'Samuel', 'name' : 'Castillo J.', 'mail' : '', 'website'  : '', 'picture' : 'samuel.png'},
            { 'first_name' : 'Elias', 'name' : 'Showk', 'mail' : '', 'website' : '', 'picture' : ''},
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
            { 'name' : 'Mines ParisTech', 'website' : 'http://mines-paristech.fr', 'picture' : 'logo.png'},
            # copy paste the line above and write your informations please
            ]

    random.shuffle(sponsors)
    return(sponsors)

