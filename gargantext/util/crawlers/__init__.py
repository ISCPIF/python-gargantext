import importlib
from gargantext.constants import RESOURCETYPES
from gargantext.settings import DEBUG
#if DEBUG: print("Loading available Crawlers")

base_parser = "gargantext.util.crawlers"
for resource in RESOURCETYPES:
    if resource["crawler"] is not None:
        try:
            name =resource["crawler"]
            #crawler is type basename+"Crawler"
            filename = name.replace("Crawler", "").lower()
            module = base_parser+".%s" %(filename)
            importlib.import_module(module,name, locals(), globals())
            #if DEBUG: print("\t-", name)
        except Exception as e:
            print("Check constants.py RESOURCETYPES declaration %s \nCRAWLER %s is not available for %s" %(str(e), resource["crawler"], resource["name"]))

#initial import
#from .cern import CernCrawler
#from .istex import ISTexCrawler
#from .pubmed import PubmedCrawler

