from gargantext.util.http import *

from django.contrib import auth


def login(request):

    logout(request)
    username = password = ''

    next_page = ""

    if request.method == "GET":
        additional_context = {}
        # if for exemple: auth/?next=/project/5/corpus/554/document/556/
        #   => we'll forward ?next="..." into template with form
        if ('next' in request.GET):
            additional_context = {'next_page':request.GET['next']}

        return render_to_response('pages/auth/login.html',
                            additional_context,
                            context_instance=RequestContext(request)
                            )

    elif request.method == "POST":
        username = request.POST['username']

        # /!\ pass is sent clear in POST data
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:

            if user.is_active:
                login(request, user)

                # if "next" forwarded from the GET via the template form
                if ('the_next_page' in request.POST):
                    return HttpResponseRedirect(request.POST['the_next_page'])
                else:
                    return HttpResponseRedirect('/projects/')


def logout(request):
    '''Logout the user, and redirect to main page
    '''
    auth.logout(request)
    return HttpResponseRedirect('/')
