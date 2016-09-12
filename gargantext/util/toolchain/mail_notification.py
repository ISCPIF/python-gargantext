
from gargantext.models.users import User
from gargantext.util.db      import session
from django.core.mail        import send_mail
from gargantext.settings     import BASE_URL

def notify_owner(corpus):
    user = session.query(User).filter(User.id == corpus.user_id).first()

    message = '''
    Bonjour,
    votre analyse sur Gargantext vient de se terminer.

    Vous pouvez accéder à votre corpus intitulé
        \"%s\"
    à l'adresse:

    http://%s/projects/%d/corpora/%d

    Nous restons à votre disposition pour tout complément d'information.
    Cordialement
    --
        L'équipe de Gargantext (CNRS)

    ''' % (corpus.name, BASE_URL, corpus.parent_id, corpus.id)
    
    if user.email != "" :
        send_mail('[Gargantext] Votre analyse est terminée'
                 , message
                 , 'team@gargantext.org'
                 , [user.email], fail_silently=False )
    else:
        print("User %s (%d), has no email" % (user.username, user.id) )



