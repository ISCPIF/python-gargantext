from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.views.generic import FormView
from django.shortcuts import redirect
from gargantext.models.users import User
from django import forms

from gargantext.views.pages.projects import overview

from gargantext.views.pages.forms import AuthenticationForm

class LoginView(FormView):
    form_class = AuthenticationForm
    success_url = reverse_lazy(overview)	#A la place de profile_view, choisir n'importe quelle vue
    template_name = 'pages/main/login.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)

        if user is not None and user.is_active:
            login(self.request, user)
            return super(LoginView, self).form_valid(form)
        else:
            return self.form_invalid(form)


def out(request):
    """Logout the user, and redirect to main page
    """
    logout(request)
    return redirect('/')
