from django.template.loader import get_template
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect

from django import forms

from urllib.parse import quote_plus as urlencode

from django.conf import settings
from sqlalchemy.orm.exc import DetachedInstanceError

from traceback import print_tb

# authentication

def requires_auth(func):
    """Provides a decorator to force authentication on a given view.
    Also passes the URL to redirect towards as a GET parameter.
    """
    def _requires_auth(request, *args, **kwargs):
        if not request.user.is_authenticated():
            url = '/auth/login/?next=%s' % urlencode(request.path)
            return redirect(url)
        try:
            # normal return the subfunction when user ok
            return func(request, *args, **kwargs)

        # user was authenticated but something made the session expire
        except DetachedInstanceError as die:
            print("===\n Detached instance error: trying to rollback session")
            print(die)
            from gargantext.util.db import session
            session.rollback()
            print("=== session rollback ok!")
            # re init the global cache (it must still have detached instances)
            from gargantext.util.db_cache import cache
            cache.clean_all()
            print("=== cache reinit ok!")
            # and relogin for safety
            url = '/auth/login/?next=%s' % urlencode(request.path)
            return redirect(url)
    return _requires_auth


# download from a given URL

import urllib.request

def get(url):
    response = urllib.request.urlopen(url)
    return response.read()


# retrieve GET parameters from a request

def get_parameters(request):
    parameters = {}
    for key, value in request.GET._iterlists():
        if key.endswith('[]'):
            parameters[key[:-2]] = value
        else:
            parameters[key] = value[0]
    return parameters


# REST

from rest_framework.views import APIView


# provide a JSON response

from gargantext.util.json import json_encoder
def JsonHttpResponse(data, status=200):
    return HttpResponse(
        content      = data.encode('utf-8') if isinstance(data, str) else \
                       json_encoder.encode(data),
        content_type = 'application/json; charset=utf-8',
        status       = status
    )


# provide exceptions for JSON APIs

from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError as ValidationException
