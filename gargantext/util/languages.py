from gargantext.constants import *



class Language:
    def __init__(self, iso2=None, iso3=None, name=None):
        self.iso2 = iso2
        self.iso3 = iso3
        self.name = name
        self.implemented = iso2 in LANGUAGES
    def __str__(self):
        result = '<Language'
        for key, value in self.__dict__.items():
            result += ' %s="%s"' % (key, value, )
        result += '>'
        return result
    __repr__ = __str__

class Languages(dict):
    def __missing__(self, key):
        key = key.lower()
        if key in self:
            return self[key]
        raise KeyError

languages = Languages()

import pycountry
pycountry_keys = (
    ('iso639_3_code', 'iso3', ),
    ('iso639_1_code', 'iso2', ),
    ('name', 'name', ),
    ('reference_name', None, ),
    ('inverted_name', None, ),
)

for pycountry_language in pycountry.languages:
    language_properties = {}
    for pycountry_key, key in pycountry_keys:
        if key is not None and hasattr(pycountry_language, pycountry_key):
            language_properties[key] = getattr(pycountry_language, pycountry_key)
    language = Language(**language_properties)
    for pycountry_key, key in pycountry_keys:
        if hasattr(pycountry_language, pycountry_key):
            languages[getattr(pycountry_language, pycountry_key).lower()] = language

# because PubMed has weird language codes:
languages['fre'] = languages['fr']
languages['ger'] = languages['de']
languages['Français'] = languages['fr']
languages['en_US'] = languages['en']
