# Without this, we couldn't use the Django environment
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext_web.settings")
os.environ.setdefault("DJANGO_HSTORE_GLOBAL_REGISTER", "False")

from admin.utils import PrintException

# database tools
from node import models
from gargantext_web.db import *
from parsing.corpustools import *


