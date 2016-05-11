from gargantext.util.http import *

import datetime
from gargantext.util.generators import paragraphs, credits


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
        },
    )


def maintenance(request):
    '''Gargantext out of service
    '''
    return render(
        template_name = 'pages/main/maintenance.html',
        request = request,
        context = {
            'user': request.user,
            'date': datetime.datetime.now(),
        },
    )
