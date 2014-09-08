
from django.shortcuts import redirect

from django.shortcuts import render

import datetime

from django.http import Http404, HttpResponse
from django.template.loader import get_template
from django.template import Context




def home(request):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    now = datetime.datetime.now()
    html = "<html><body>Il est %s.</body></html>" % now
    return HttpResponse(html)


