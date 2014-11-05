"""
Django settings for gargantext_web project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_PATH = os.path.join(BASE_DIR, os.pardir)
PROJECT_PATH = os.path.abspath(PROJECT_PATH)



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'bt)3n9v&a02cu7^^=+u_t2tmn8ex5fvx8$x4r*j*pb1yawd+rz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes
    # Don't forget to use absolute paths, not relative paths.
    '/srv/gargantext/templates',

#import os.path
#
#TEMPLATE_DIRS = (
#    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
#)
)


#ALLOWED_HOSTS = ['*',]
ALLOWED_HOSTS = ['localhost', 'master.polemic.be', 'mat.polemic.be', 'alexandre.polemic.be']



# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    #'south',
    #'documents',
    'cte_tree',
    'node',
    'ngram',
    'django_hstore',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gargandb',
        'USER': 'pksm3',
        'PASSWORD': 'C8kdcUrAQy66U',
        #'USER': 'gargantext',
        #'PASSWORD': 'C8krdcURAQy99U',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

ROOT_URLCONF = 'gargantext_web.urls'

STATIC_ROOT = '/var/www/gargantext/static/'
STATIC_URL = '/static/'

MEDIA_ROOT = '/var/www/gargantext/media'
#MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')
MEDIA_URL   = '/media/'


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)


STATICFILES_DIRS = (
            #os.path.join(BASE_DIR, "static"),
                '/srv/gargantext/static',
                #'/var/www/www/alexandre/media',
                #'/var/www/alexandre.delanoe.org/',
                )

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
    "django.core.context_processors.static",
)




# grappelli custom
GRAPPELLI_ADMIN_TITLE = "Gargantext"
