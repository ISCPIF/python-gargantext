from gargantext.util.http import *

from django.contrib import auth


def login(request):
    """Performs user login
    """
    auth.logout(request)

    # if the user send her authentication data to the page
    if request.method == "POST":
        # /!\ pass is sent clear in POST data: use SSL
        user = auth.authenticate(
            username = request.POST['username'],
            password = request.POST['password']
        )
        if user is not None and user.is_active:
            auth.login(request, user)
            # if "next" forwarded from the GET via the template form
            if 'the_next_page' in request.POST:
                return redirect(request.POST['the_next_page'])
            else:
                return redirect('/projects/')

    # if the user wants to access the login form
    additional_context = {}
    # if for exemple: auth/?next=/project/5/corpus/554/document/556/
    #   => we'll forward ?next="..." into template with form
    if 'next' in request.GET:
        additional_context = {'next_page':request.GET['next']}

    return render(
        template_name = 'pages/auth/login.html',
        request = request,
        context = additional_context,
    )


def logout(request):
    """Logout the user, and redirect to main page
    """
    auth.logout(request)
    return redirect('/')
