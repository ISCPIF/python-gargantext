from django.conf.urls import patterns, url
from graphExplorer import views

# /!\ urls patterns here are *without* the trailing slash

urlpatterns = patterns('',
    url(r'^register/$', views.Register.as_view()), # Register
    url(r'^login/$', views.Login.as_view()),       # Login

)
