#version2
#imported as needed

#Version 1
#~ import importlib
#~ from gargantext.constants import LANGUAGES
#~ from gargantext.settings import DEBUG


#~ if DEBUG:
    #~ print("Loading available Taggers:")

#~ for lang, tagger in LANGUAGES.items():
    #~ tagger = tagger["tagger"]
    #~ filename = "gargantext.util.taggers.%s" %(tagger)
    #~ if DEBUG:
        #~ print("\t-%s (%s)" %(tagger, lang))
    #~ getattr(importlib.import_module(filename), tagger)()


#VERSION 0
#~ #initally a manual import declaration
#~ from .TurboTagger import TurboTagger
#~ from .NltkTagger import NltkTagger
#~ from .TreeTagger import TreeTagger
#~ from .MeltTagger import EnglishMeltTagger, FrenchMeltTagger
