
from gargantext.util.http import render

def home(request):
    '''Home describes the platform.
    A video draws the narratives.
    If not logged a project test is shown.
    '''
    return render(
        template_name = 'pages/main/home.html',
        request = request,
#        context = {
#            'debug': settings.DEBUG,
#            'user': request.user,
#            'date': datetime.datetime.now(),
#            'paragraph_gargantua': paragraphs.gargantua(),
#            'paragraph_lorem' : paragraphs.lorem(),
#            'paragraph_tutoreil': paragraphs.tutoreil(),
#            'languages': USER_LANG,
#            'user_parameters': get_user_params(request.user)
#        },
    )

