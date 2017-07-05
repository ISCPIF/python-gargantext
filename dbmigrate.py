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

    # migrate SQLAlchemy models
    from gargantext.models import Base
    from gargantext.util.db import engine
    sqla_models = (
        Base.metadata.tables[model_name]
        for model_name in Base.metadata.tables.keys()
    )
    print()
    for model in sqla_models:
        try:
            model.create(engine)
            print('created model: `%s`' % model)
        except Exception as e:
            print('could not create model: `%s`, %s' % (model, e))
        print()
