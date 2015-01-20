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
            { 'first_name' : 'Alexandre', 'last_name' : 'Delanoë', 'mail' : 'alexandre+gargantextATdelanoe.org', 'website' : 'http://alexandre.delanoe.org', 'picture' : 'alexandre.jpg'},
            { 'first_name' : 'David', 'last_name' : 'Chavalarias', 'mail' : '', 'website' : 'http://chavalarias.com', 'picture' : 'david.jpg'},
            { 'first_name' : 'Mathieu', 'last_name' : 'Rodic', 'mail' : '', 'website'  : 'http://rodic.fr', 'picture' : 'mathieu.jpg'},
            { 'first_name' : 'Samuel', 'last_name' : 'Castillo J.', 'mail' : '', 'website'  : '', 'picture' : 'samuel.jpg'},
            { 'first_name' : 'Elias', 'last_name' : 'Showk', 'mail' : '', 'website' : '', 'picture' : 'logo.svg'},
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

