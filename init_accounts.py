#!/usr/bin/env python
import sys
import os

dirname = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext.settings")

# initialize Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


from django.contrib.auth import password_validation
from django.contrib.auth.hashers import ( check_password
                                        , is_password_usable
                                        , make_password
                                        )
from django.db import models
from django.utils.crypto import get_random_string, salted_hmac


# retrieve Django models
import django.apps
django_models = django.apps.apps.get_models()
django_models_names = set(model._meta.db_table for model in django_models)


from gargantext.util.db      import session
from gargantext.models.users import User, Contact
from django.core.mail        import send_mail
from gargantext.settings     import BASE_URL

drafts = {
        'partnerOk' : '''
        Bonjour,

        Vous avez fait une demande d'accès à la plate-forme
        Gargantext. L'équipe de l'ISC-PIF a tout mis en œuvre pour
        vous donner accès à cette plate-forme dans les meilleurs
        délais.

        Nous vous recommendons de prendre connaissance des conditions
        d'utilisation de la plate-forme à l'adresse ci-dessous en
        attirant votre attention sur les points suivants :

        1 - L'usage de cette plate-forme est réservé à un cadre académique,

        2 - Le service Gargantext est un service d'analyse de données,
        et non de stockage. Il appartient à chaque utilisateur
        d'assurer la sauvegarde de ses propres données et résultats en
        les téléchargeant à partir de la plate-forme.

        3 - La réutilisation des données, graphiques, analyses et
        cartographies générés par Gargantext dans toute publication
        et communication suppose la mention explicite de Gargantext et
        de l'ISC-PIF CNRS comme par exemple : "ces résultats ont été
        obtenus à l'aide de du logiciel Gargantext développé par
        ISC-PIF/CNRS".

        Lire l'intégralité des conditions d'utilisation (recommandé) sur :
        http://gitlab.iscpif.fr/humanities/tofu/tree/master
        
        Vous pouvez vous connecter à l'adresse:
                http://%s
        
        Avec les identifiants suivants:
        Votre login est: %s
        Votre mot de passe est : %s

        Vous êtes actuellement sur cette version stabilisée pour une
        expérience unique dans l'exploration de vos thèmes de recherche.

        Vos retours seront précieux pour poursuivre le développement
        de la plateforme, n'hésitez pas à nous contacter et
        contribuer!

        Si vous souhaitez accéder à vos anciens corpus, vos anciens
        codes d'accès restent valides à cette adresse jusqu'au 30 juin
        2017 minuit:

                http://old.gargantext.org

        Nous restons à votre disposition pour tout complément d'information.
        Cordialement
        --
            L'équipe de Gargantext (CNRS)

        '''
        ,

        'partnerKo' : '''
        Bonjour,

        Vous venez de faire une demande d'accès à la plate-forme
        Gargantext, développée et hébergée grâce au soutien du CNRS
        et des partenaires de l'ISC-PIF. L'équipe de l'ISC-PIF a tout
        mis en œuvre pour vous donner accès à cette plate-forme dans
        les meilleurs délais.

        Cette plate-forme étant accessible en priorité au personnel
        des établissements partenaires de l'ISC-PIF, nous vous
        proposons un accès pour une durée de 3 mois afin que vous
        puissiez explorer les possibilités de Gargantext. S'il s'avère
        que cette plateforme correspond à vos besoins, vous pourrez
        vous prendre contact avec le service partenariat de l'ISC-PIF
        (contact@gargantext.org) pour étudier une adhésion de votre
        établissement à l'ISC-PIF ou bien vous rapprocher de votre
        établissement afin qu'il déploie une instance de Gargantext.

        Nous vous invitons à prendre connaissance des conditions
        d'utilisation de la plate-forme à l'adresse ci-dessous en
        attirant votre attention sur les points suivants :

        1 - L'usage de cette plate-forme est réservé à un cadre académique,

        2 - Le service Gargantext est un service d'analyse de données,
        et non de stockage. Il appartient à chaque utilisateur
        d'assurer la sauvegarde de ses propres données et résultats en
        les téléchargeant à partir de la plate-forme.

        3 - La réutilisation des données, graphiques, analyses et
        cartographies générés par Gargantext dans toute publication
        et communication suppose la mention explicite de Gargantext et
        de l'ISC-PIF CNRS comme par exemple : "ces résultats ont été
        obtenus à l'aide de du logiciel Gargantext développé par
        ISC-PIF/CNRS".

        Lire l'intégralité des conditions d'utilisation (recommandé) sur :
        http://gitlab.iscpif.fr/humanities/tofu/tree/master

        Vous pouvez donc vous connecter à l'adresse:
                http://%s
        
        Avec les identifiants suivants:
        Votre login est: %s
        Votre mot de passe est : %s

        Vous êtes actuellement sur cette version stabilisée pour une
        expérience unique dans l'exploration de vos thèmes de recherche.

        Vos retours seront précieux pour poursuivre le développement
        de la plateforme, n'hésitez pas à nous contacter et
        contribuer!

        Nous restons à votre disposition pour tout complément d'information.
        Cordialement
        --
            L'équipe de Gargantext (CNRS)

        ''' ,

        }

def make_random_password(length=10
                         , allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                         'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                         '0123456789'):
    """
    Generate a random password with the given length and given
    allowed_chars. The default value of allowed_chars does not have "I" or
    "O" or letters and digits that look similar -- just to avoid confusion.
    (source: django/contrib/auth)
    """
    return get_random_string(length, allowed_chars)

def mail2user(username, email, password, draft):
    send_mail ('[Gargantext] Votre accès à la plateforme'
              , draft % (BASE_URL, username, password)
              , 'team@gargantext.org'
              , [email]
              , fail_silently=False 
              )

def block(user1_id, user2_id, bool_):
    '''
    user_group :: Int -> Int -> Bool
    Link between user1 and user2
    If False: 
        link blocked
    else:
        link not blocked

    '''
    contact = Contact()
    
    contact.user1_id   = user1_id
    contact.user2_id   = user2_id
    contact.is_blocked = bool_

    session.add(contact)
    session.commit()
    
    return contact

def create_user(username, email, user=None, password=None, group=None, notify=False):
    '''
    create_user :
        - create user
        - create its group if needed
        - create relation between user and its group

    '''
    if user is None:
        user = User()
    
    user.username    = username
    user.email       = email
    user.is_active   = True
    
    # Creating the password
    if password is None or len(password) < 3 :
        password = make_random_password()
    user.password = make_password(password)

    session.add(user)
    session.commit()

    if group is not None :
        # get or create group_iscpif
        group_iscpif_id = session.query(User.id).filter(User.username=="group_iscpif").first()
        
        if group_iscpif_id is None:
            group_iscpif    = create_user("group_iscpif", "group@gargantext.org", group=None, notify=False)
            group_iscpif_id = group_iscpif.id

        if group == "group_iscpif":
            block (user.id, group_iscpif_id, False)
        else:
            block (user.id, group_iscpif_id, True)


    if notify == True and group == "group_iscpif" :
        mail2user (username, email, password, drafts['partnerOk'])
    elif notify == True :
        mail2user (username, email, password, drafts['partnerKo'])
    else:
        print("User %s created, no notification" % username)

    return user

def del_user(username):
    '''
    del_user :: String -> ()
    '''
    print("Test is True, deleting username %s" % username)
    session.query(User).filter(User.username == username).delete()

def active_user(username, bool_=True):
    '''
    active_user :: String -> Maybe Bool -> ()
    if bool_ == True:
        user is active
    else:
        user is not active
    '''
    user = session.query(User).filter(User.username == username).first()
    user.is_active = bool_
    user.save()

def mass_account_creation(csv_file=None, init=False, test=False, notify=False):
    '''
    CSV file as parameter:
    if partner:
        username,email@example.com,group_iscpif,password,
    else:
        username,email@example.com,group_others,password,
    '''
    accounts = open(csv_file, "r")
    for line in accounts.readlines():
        username, email, group, password, end = line.split(',')
        user = session.query(User).filter(User.username == username).first()

        if user is not None:
            if init == True:
                create_user(username, email, user=user, group=group, password=password, notify=notify)
                print("User %s exists and updated" % (username))
            else:
                print("User %s exists and not updated" % (username))

        else:
            create_user(username, email, group=group, password=password, notify=notify)
            print("User %s is created" % (username))
        
        if test==True:
            del_user(username)
            del_user(group)
    
    accounts.close()

if __name__ == "__main__":
    mass_account_creation(csv_file=sys.argv[1], init=True, notify=True, test=False)


