#!/usr/bin/env python
import sys
import os

if __name__ == "__main__":

    # Django settings
    dirname = os.path.dirname(os.path.realpath(__file__))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext.settings")

    # initialize Django application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    # retrieve Django models
    import django.apps
    django_models = django.apps.apps.get_models()
    django_models_names = set(model._meta.db_table for model in django_models)

    # migrate SQLAlchemy models
    from gargantext import models
    from gargantext.util.db import Base, engine
    sqla_models_names = (
        model for model in Base.metadata.tables.keys()
        if model not in django_models_names
    )
    sqla_models = (
        Base.metadata.tables[model_name]
        for model_name in sqla_models_names
    )
    print()
    for model in sqla_models:
        try:
            model.create(engine)
            print('created model: `%s`' % model)
        except Exception as e:
            print('could not create model: `%s`, %s' % (model, e))
        print()
