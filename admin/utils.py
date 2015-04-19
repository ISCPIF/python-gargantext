import os, sys
import linecache

from gargantext_web.settings import MEDIA_ROOT

def ensure_dir(user):
    '''
    If user is new, folder does not exist yet, create it then
    '''
    dirpath = '%s/corpora/%s' % (MEDIA_ROOT, user.username)
    if not os.path.exists(dirpath):
        print("Creating folder %s" % dirpath)
        os.makedirs(dirpath)


def PrintException():
    '''
    This function has to be used in except part to print error with:
    - the file
    - the line number
    - an explicit error araising
    '''
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

