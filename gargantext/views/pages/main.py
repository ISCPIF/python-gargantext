from gargantext.util.http import *

import datetime
from gargantext.util.generators import paragraphs, credits


def home(request):
    '''Home describes the platform.
    A video draws the narratives.
    If not logged a project test is shown.
    '''
    template = get_template('pages/main/home.html')
    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
        'debug': settings.DEBUG,
        'user': user,
        'date': date,
        'paragraph_gargantua': paragraphs.gargantua(),
        'paragraph_lorem' : paragraphs.lorem(),
        'paragraph_tutoreil': paragraphs.tutoreil(),
    }))
    return HttpResponse(html)


def about(request):
    '''About Gargantext, its team and sponsors
    '''
    template    = get_template('pages/main/about.html')
    user        = request.user
    date        = datetime.datetime.now()

    html = template.render(Context({
        'user': user,
        'date': date,
        'team': credits.members(),
        'institutions': credits.institutions(),
        'labos': credits.labs(),
        'grants': credits.grants(),
    }))

    return HttpResponse(html)


def maintenance(request):
    '''Gargantext out of service
    '''
    template    = get_template('pages/main/maintenance.html')
    user        = request.user
    date        = datetime.datetime.now()

    html = template.render(Context({\
            'user': user,\
            'date': date,\
            }))

    return HttpResponse(html)
