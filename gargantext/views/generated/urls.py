from django.conf.urls import include, url


from . import css, img


urlpatterns = [
    url(r'^img/logo\.svg$', img.logo),
    url(r'^css/bootstrap\.css', css.bootstrap),
]
