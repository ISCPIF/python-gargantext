from django.template.loader import get_template
from django.template import Context, RequestContext
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response,redirect

from urllib.parse import quote_plus as urlencode

from gargantext import settings


def requires_auth(func):
    def _requires_auth(request, *args, **kwargs):
        if not request.user.is_authenticated():
            url = '/auth/login/?next=%s' % urlencode(request.path)
            return redirect(url)
        return func(request, *args, **kwargs)
    return _requires_auth
