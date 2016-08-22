import importlib
from gargantext.constants import RESOURCETYPES
from gargantext.settings import DEBUG
if DEBUG:
    print("Loading available PARSERS:")
base_parser = "gargantext.util.parsers"
for resource in RESOURCETYPES:
    if resource["parser"] is not None:
        #parser file is without Parser
        fname = resource["parser"].replace("Parser", "")
        #parser file is formatted as a title
        module = base_parser+".%s" %(fname.upper())
        #parser module is has shown in constants
        parser = importlib.import_module(module)
        if DEBUG:
            print("\t-", resource["parser"])
        getattr(parser,resource["parser"])
