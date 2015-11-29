
import threading
from queue import Queue
# import time


import random
from gargantext_web.db import session, Node_Ngram

class ChunkedSELECTS:

    def __init__(self):
        self.q = Queue()
        self.firstResults = []
        self.lock = threading.Lock() # lock to serialize console output
        self.ngrams_dict = {}

    def worker_sql_action(self , docs_list):
        data = {}
        for d in docs_list:
            # this_ngrams = session.query(Node_Ngram.ngram_id).filter( Node_Ngram.node_id==d).all()
            this_ngrams = session.query(Node_Ngram.ngram_id,Node_Ngram.weight).filter( Node_Ngram.node_id==d).all()
            filtered_ngrams = []
            for n in this_ngrams:
                if n[0] in self.ngrams_dict:
                    # filtered_ngrams.append(  n[0] )
                    filtered_ngrams.append( [ n[0] , int(n[1]) ] )
            data[d] = filtered_ngrams
        with self.lock:
            # print(threading.current_thread().name, str(len(docs_list))+" OK")
            return data


    def worker_sql(self):
        while True:
            item = self.q.get()
            results = []
            try: 
                result = self.worker_sql_action(item)
            except: 
                result = False
            self.firstResults.append(result)
            self.q.task_done()

    def chunks(self , l , n):
        for i in range(0, len(l), n):
            yield l[i:i+n]
