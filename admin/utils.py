import os, sys
import linecache
from time import time

from gargantext_web.settings import MEDIA_ROOT
from django.db import connection

class DebugTime:
    def __init__(self, prefix):
        self.prefix = prefix
        self.message = None
        self.time = None

    def __del__(self):
        if self.message is not None and self.time is not None:
            print('%s - %s: %.4f' % (self.prefix, self.message, time() - self.time))

    def show(self, message):
        self.__del__()
        self.message = message
        self.time = time()

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


class WorkflowTracking:
    def __init__( self ):
        self.hola = "mundo"

    def processing_(self , corpus_id , step):
        try:
            the_query = """ UPDATE node_node SET hyperdata=\'{ \"%s\" : \"%s\"}\' WHERE id=%d """ % ( "Processing", step , corpus_id )
            cursor = connection.cursor()
            try:
                cursor.execute(the_query)
                cursor.execute("COMMIT;")
            finally:
                connection.close()
        except :
            PrintException()
