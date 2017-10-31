
from gargantext.models.users import User
from gargantext.util.db      import session
from django.core.mail        import send_mail
from gargantext.settings     import BASE_URL

def notify_owner(corpus,cooc_id,distance,bridgeness):
    user = session.query(User).filter(User.id == corpus.user_id).first()

    message = '''
    Bonjour,
    votre graph vient de se terminer dans votre corpus intitulé:
                        %s

    Vous pouvez accéder et renommer votre Graph à l'adresse:
    http://%s/projects/%d/corpora/%d/explorer?cooc_id=%d&distance=%s&bridgeness=%d

    Nous restons à votre disposition pour tout complément d'information.
    Cordialement
    --
        L'équipe de Gargantext (CNRS)

    ''' % (corpus.name, BASE_URL, corpus.parent_id, corpus.id, cooc_id, distance, bridgeness)
    
    if user.email != "" :
        send_mail('[Gargantext] Votre Graph est calculé'
                 , message
                 , 'team@gargantext.org'
                 , [user.email], fail_silently=False )
    else:
        print("User %s (%d), has no email" % (user.username, user.id) )



