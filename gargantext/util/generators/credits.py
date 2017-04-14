# -*- coding: utf-8 -*-

# Order in script: Alphabetical order (first_name, name, mail, website)
# Order in public: Shuffled order

import random


_members = [

    { 'first_name' : 'David', 'last_name' : 'Chavalarias',
     'mail' : 'david.chavalariasATiscpif.fr',
     'website' : 'http://chavalarias.com',
     'picture' : 'david.jpg',
     'role':'principal investigator'},

    { 'first_name' : 'Samuel', 'last_name' : 'Castillo J.',
     'mail' : 'kaisleanATgmail.com',
     'website'  : 'http://www.pksm3.droppages.com',
     'picture' : 'samuel.jpg',
     'role' : 'developer'},

    { 'first_name' : 'Maziyar', 'last_name' : 'Panahi',
     'mail' : '',
     'website'  : 'http://iscpif.fr',
     'picture' : 'maziyar.jpg',
     'role' : 'developer'},

    { 'first_name' : 'Alexandre', 'last_name' : 'Delanoë',
     'mail' : 'alexandre+gargantextATdelanoe.org',
     'website' : 'http://alexandre.delanoe.org',
     'picture' : 'alexandre.jpg',
     'role' : 'project manager'},

    #{ 'first_name' : '', 'name' : '', 'mail' : '', 'website' : '', 'picture' : ''},
    # copy-paste the line above and write your informations please
]

_membersPast = [
    { 'first_name' : 'Constance', 'last_name' : 'de Quatrebarbes',
     'mail' : '4barbesATgmail.com',
     'website'  : 'http://c24b.github.io/',
     'picture' : 'constance.jpg',
     'role' : 'developer'},

     { 'first_name' : 'Mathieu', 'last_name' : 'Rodic',
     'mail' : '',
     'website'  : 'http://rodic.fr',
     'picture' : 'mathieu.jpg',
     'role' : 'developer'},
        
    { 'first_name' : 'Romain', 'last_name' : 'Loth',
     'mail' : '',
     'website'  : 'http://iscpif.fr',
     'picture' : 'romain.jpg',
     'role' : 'developer'},

    { 'first_name' : 'Elias', 'last_name' : 'Showk',
     'mail' : '',
     'website' : 'https://github.com/elishowk',
     'picture' : '', 'role' : 'developer'},
        ]

_institutions = [
    { 'name' : 'Mines ParisTech', 'website' : 'http://mines-paristech.fr', 'picture' : 'mines.png', 'funds':''},
    #{ 'name' : 'Institut Pasteur', 'website' : 'http://www.pasteur.fr', 'picture' : 'pasteur.png', 'funds':''},
    { 'name' : 'EHESS', 'website' : 'http://www.ehess.fr', 'picture' : 'ehess.png', 'funds':''},
    #{ 'name' : '', 'website' : '', 'picture' : '', 'funds':''},
    # copy paste the line above and write your informations please
]

_labs = [
    { 'name' : 'Centre de Sociologie de l\'innovation', 'website' : 'http://www.csi.mines-paristech.fr/en/', 'picture' : 'csi.png', 'funds':''},
    #{ 'name' : '', 'website' : '', 'picture' : '', 'funds':''},
    # copy paste the line above and write your informations please
]

_grants = [
    { 'name' : 'Institut Mines Telecom', 'website' : 'https://www.imt.fr', 'picture' : 'IMT.jpg', 'funds':''},
    { 'name' : 'Forccast', 'website' : 'http://forccast.hypotheses.org/', 'picture' : 'forccast.png', 'funds':''},
    { 'name' : 'Mastodons', 'website' : 'http://www.cnrs.fr/mi/spip.php?article53&lang=fr', 'picture' : 'mastodons.png', 'funds':''},
    #{ 'name' : 'ADEME', 'website' : 'http://www.ademe.fr', 'picture' : 'ademe.png', 'funds':''},
    #{ 'name' : '', 'website' : '', 'picture' : '', 'funds':''},
    # copy paste the line above and write your informations please
]


def members():
    random.shuffle(_members)
    return _members

def membersPast():
    random.shuffle(_membersPast)
    return _membersPast

def institutions():
    random.shuffle(_institutions)
    return _institutions

def partners():
    random.shuffle(_partners)
    return _partners

def labs():
    random.shuffle(_labs)
    return _labs

def grants():
    random.shuffle(_grants)
    return _grants
