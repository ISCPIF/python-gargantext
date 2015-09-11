# Without this, we couldn't use the Django environment
from admin.env import *

from gargantext_web.views import empty_trash
empty_trash()

