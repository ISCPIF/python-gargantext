from node.models import User
from django.core.mail import send_mail

def notify_user(username, email, password):
    message = '''
    Bonjour,
    voici votre compte.
    Veuillez vous connecter à
    http://beta.gargantext.org

    Votre login: %s
    Votre mot de passe : %s

    Je reste à votre disposition pour tout complément d'information.
    Cordialement
    --
        Alexandre Delanoë

    ''' % (username, password)

    #send_mail('[Gargantext] Votre compte', message, 'alexandre.delanoe@mines-paristech.fr', [email], fail_silently=False )
    send_mail('[Gargantext] Votre compte', message, 'alexandre.delanoe@mines-paristech.fr', [email], ['alexandre+gargantext@delanoe.org'] )
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

def mines_account_creation(fichier=None):
    if file is None:
        fichier = "/home/alexandre/projets/forccast/Tutorat/2014-2015/comptes_gargantext.txt"
    accounts = open(fichier, "r")
    for line in accounts.readlines():
        username, email, password = line.split(',')
        #create_user(username, email, password=password, notify=True)
        delete_user(username)
    fichier.close()

