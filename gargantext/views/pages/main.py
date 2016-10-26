from gargantext.util.http       import *
from gargantext.util.db         import session
from gargantext.models          import Node, User
import datetime
from gargantext.util.generators import paragraphs, credits

def get_node_user(user):
    #load user parameters from User(Node).hyperdata from request.user or cache.
    node_user = session.query(Node).filter(Node.user_id == user.id, Node.typename== "USER").first()

    if node_user is None:
        try:
            node_user = Node(
                user_id = user.id,
                typename = 'USER',
                name = user.name,
            )
        except AttributeError:
            node_user = Node(
                user_id = user.id,
                typename = 'USER',
                name = "Anne Aunime",
            )
        #default language for now is  'fr'
        node_user.hyperdata.language = "fr"
        session.add(node_user)
        session.commit()
    return node_user

def home(request):
    '''Home describes the platform.
    A video draws the narratives.
    If not logged a project test is shown.
    '''
    user_node = get_node_user(request.user)
    return render(
        template_name = 'pages/main/home.html',
        request = request,
        context = {
            'debug': settings.DEBUG,
            'user': request.user,
            'date': datetime.datetime.now(),
            'paragraph_gargantua': paragraphs.gargantua(),
            'paragraph_lorem' : paragraphs.lorem(),
            'paragraph_tutoreil': paragraphs.tutoreil(),
            'user_parameters': user_node.hyperdata

        },
    )

def about(request):
    '''About Gargantext, its team and sponsors
    '''
    user_node = get_user_node(request.user)
    return render(
        template_name = 'pages/main/about.html',
        request = request,
        context = {
            'user': request.user,
            'date': datetime.datetime.now(),
            'team': credits.members(),
            'institutions': credits.institutions(),
            'labos': credits.labs(),
            'grants': credits.grants(),
            'user_parameters': user_node.hyperdata
        },
    )

def robots(request):
    '''Robots rules
    '''
    return render(
        template_name = 'pages/main/robots.txt',
        request = request,
        content_type='text/plain',
    )

def maintenance(request):
    '''Gargantext out of service
    '''
    user_node = get_user_node(request.user)
    return render(
        template_name = 'pages/main/maintenance.html',
        request = request,
        context = {
            'user': request.user,
            'date': datetime.datetime.now(),
            'user_parameters': user_node.hyperdata
        },
    )
