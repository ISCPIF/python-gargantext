import os
from gargantext_web.settings import MEDIA_ROOT

def ensure_dir(user):
# If user is new, folder does not exist yet, create it then
    dirpath = '%s/corpora/%s' % (MEDIA_ROOT, user.username)
    if not os.path.exists(dirpath):
        print("Creating folder %s" % dirpath)
        os.makedirs(dirpath)


