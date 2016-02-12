from django.template.loader import get_template
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect

from django import forms

from urllib.parse import quote_plus as urlencode

from gargantext import settings


def requires_auth(func):
    """Provides a decorator to force authentication on a given view.
    Also passes the URL to redirect towards as a GET parameter.
    """
    def _requires_auth(request, *args, **kwargs):
        if not request.user.is_authenticated():
            url = '/auth/login/?next=%s' % urlencode(request.path)
            return redirect(url)
        return func(request, *args, **kwargs)
    return _requires_auth
