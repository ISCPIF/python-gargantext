from gargantext.util.http       import *
from gargantext.util.db         import session
from gargantext.models          import Node, User
import datetime
from gargantext.util.generators import paragraphs, credits
from gargantext.constants       import USER_LANG

def get_user_node(user):
    if user.is_authenticated:
        node_user = session.query(Node).filter(Node.user_id == user.id, Node.typename== "USER").first()
        return node_user
    else:
        return None
def get_user_params(user):
    node_user = get_user_node(user)
    if node_user is not None:
        return node_user.hyperdata
    return {}

def home(request):
    '''Home describes the platform.
    A video draws the narratives.
    If not logged a project test is shown.
    '''
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
            'languages': USER_LANG,
            'user_parameters': get_user_params(request.user)
        },
    )

def about(request):
    '''About Gargantext, its team and sponsors
    '''

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
            'user_parameters': get_user_params(request.user),
            'languages': USER_LANG,
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
            'user_parameters': get_user_params(request.user)
        },
    )
