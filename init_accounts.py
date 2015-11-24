from admin.env import *
import sys
from node.models import User
from django.core.mail import send_mail

def notify_user(username, email, password):
    message = '''
    Bonjour,
    votre compte vient d'être créé.

    Vous pouvez désormais vous connecter ici:
    http://mines.gargantext.org

    Votre login est: %s
    Votre mot de passe est : %s

    Nous restons votre disposition pour tout complément d'information.
    Cordialement
    --
        L'équipe de Gargantext (CNRS)

    ''' % (username, password)

    send_mail('[Gargantext] Création de votre compte', message, 'alexandre.delanoe@mines-paristech.fr', [email], fail_silently=False )
    #send_mail('[Gargantext] Votre compte', message, 'alexandre.delanoe@mines-paristech.fr', [email], ['alexandre@delanoe.org'] )


    # add option for mass sending email

def create_user(username, email, password=None, active=False, notify=True):
    user = User()
    user.username = username
    user.email = email
    user.active_user = active
    if password is None:
        password = User.objects.make_random_password()
        print(password)
    user.set_password(password)
    user.save()
    
    if notify == True:
        notify_user(username, email, password)
    
    return user

def delete_user(username):
    user = User.objects.get(username=username)
    user.delete()

def active_user(username, active=True):
    '''
    To get inactive, active=False
    '''
    user = User.objects.get(username=username)
    user.active_user = active
    user.save()

def mass_account_creation(fichier=None):
    if fichier is None:
        fichier = "/tmp/comptes.csv"
    accounts = open(fichier, "r")
    for line in accounts.readlines():
        username, email, password, fin = line.split(',')
        create_user(username, email, password=password, active=True, notify=False)
        #delete_user(username)
    accounts.close()

if __name__ == "__main__":
    mass_account_creation(fichier=sys.argv[1])


