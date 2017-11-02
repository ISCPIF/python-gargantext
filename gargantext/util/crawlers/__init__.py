import importlib
from django.conf import settings
from gargantext.constants import RESOURCETYPES

#if settings.DEBUG: print("Loading available Crawlers")

base_parser = "gargantext.util.crawlers"
for resource in RESOURCETYPES:
    if resource["crawler"] is not None:
        try:
            name =resource["crawler"]
            #crawler is type basename+"Crawler"
            filename = name.replace("Crawler", "").upper()
            module = base_parser+".%s" %(filename)
            importlib.import_module(module)

            #if settings.DEBUG: print("\t-", name)
        except Exception as e:
            print("Check constants.py RESOURCETYPES declaration %s \nCRAWLER %s is not available for %s" %(str(e), resource["crawler"], resource["name"]))

#initial import
#from .cern import CernCrawler
#from .istex import ISTexCrawler
#from .pubmed import PubmedCrawler

