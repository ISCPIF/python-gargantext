"""Cache management
Allows retrieval of an instance from the value of one of its primary or unique
keys, without querying the database.
"""

from sqlalchemy import or_

from gargantext.util.db import *
from gargantext import models


class ModelCache(dict):

    def __init__(self, model, preload=False):
        self._model = model
        self._columns = [column for column in model.__table__.columns if column.unique or column.primary_key]
        self._columns_names = [column.name for column in self._columns]
        if preload:
            self.preload()

    def __missing__(self, key):
        formatted_key = None
        conditions = []
        for column in self._columns:
            try:
                formatted_key = column.type.python_type(key)
                conditions.append(column == key)
            except ValueError as e:
                continue
        if formatted_key in self:
            self[key] = self[formatted_key]
        else:
            element = session.query(self._model).filter(or_(*conditions)).first()
            if element is None:
                raise KeyError
            self[key] = element
        return element

    def preload(self):
        self.clear()
        for element in session.query(self._model).all():
            for column_name in self._columns_names:
                key = getattr(element, column_name)
                self[key] = element

class Cache:

    def __getattr__(self, key):
        '''
        lazy init of new modelcaches: self.Node, self.User...
        '''
        try:
            model = getattr(models, key)
        except AttributeError:
            raise AttributeError('No such model: `%s`' % key)
        modelcache = ModelCache(model)
        setattr(self, key, modelcache)
        return modelcache


    def clean_all(self):
        '''
        re-init any existing modelcaches
        '''
        for modelname in self.__dict__:
            old_modelcache = getattr(cache, modelname)
            new_modelcache = ModelCache(old_modelcache._model)
            del old_modelcache
            setattr(cache, modelname, new_modelcache)

cache = Cache()
