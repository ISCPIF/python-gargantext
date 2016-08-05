#!/usr/bin/python3 env
"""
TOOLCHAIN TEST SUITE
"""
#switching to standard testing
from django.test import TestCase
from django.test import Client

#from django.contrib.auth.models import User
#from django.contrib.auth import authenticate
# test Nodes
from gargantext.models import Node
from gargantext.constants import RESOURCETYPES, NODETYPES
# provides GargTestRunner.testdb_session
from unittests.framework import GargTestRunner
import os
DATA_SAMPLE_DIR = "/srv/gargantext_lib/data_samples/"

class ToolChainRecipes(TestCase):
    def setUp(self):
        self.session = GargTestRunner.testdb_session
        self.client = Client()

        # login ---------------------------------------------------
        response = self.client.post(
              '/auth/login/',
              {'username': 'gargantua', 'password': 'gargantua'}
           )
        # ---------------------------------------------------------
        self.source_list = [(resource["type"], resource["name"]) for resource in RESOURCETYPES]
        self.source_list.insert(0, (0,"Select a database below"))
        #self.files = for d in os.path.join("/home/")
        self.sample_files = self._collect_samples_files()

    def tearDown(self):
        del self.session
        del self.client
        del self.source_list
        del self.file_list
    def list_data_samples(self):
        pass

    def _create_project(self):
        self.project = Node(
            user_id = user.id,
            typename = 'PROJECT',
            name = "test1",
        )
        session.add(self.project)
        session.commit()
        return self.project

    def create_test(self):
        #need a file a name and a sourcetype
        pass

    def __create_user__(self, name="john", password="lucyinthesky", mail='lennon@thebeatles.com'):
        user = User.objects.create_user(name, mail, password)
        user.save()
        self.user = User.objects.get(name="john")
        return self.user

    def __find_node__(self, typename, name=None):
        '''find a node by typenode and name'''
        if name is not None:
            self.node = self.session.query(Node).filter(Node.typename == typename, Node.name == name).first()
        else:
            self.node = self.session.query(Node).filter(Node.typename == typename).first()
    def __find_nodes__(self, typename):
        '''find nodes by typename'''
        self.nodes = self.session.query(Node).filter(Node.typename == typename).all()
    def __find_node_children__(self, CurrNode, typename=None):
        '''find ALL the children of a given Node [optionnal filter TYPENAME] '''
        if typename is None:
            self.children = CurrNode.children('', order=True).all()
        else:
            self.children = CurrNode.children(typename, order=True).all()
    def __find_node_parent__(self, CurrNode):
        '''find the parent Node given a CurrNode '''
        self.parent = self.session.query(Node).filter(Node.id == Node.parent_id, Node.name == name).first()

    def __get_statuses__(self, Node):
        '''get the status of the current Node'''
        self.statuses = Node.get_status()

        source_type = 1

        for i,sample_file in enumerate(self.sample_files["europresse"]):
            name = "testEuropress_"+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 4)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])

    def tests_002(self):
        #create a project
        source_type = 2
        source = get_resource(2)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")

        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)


        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_003(self):
        #create a project
        source_type = 3
        source = get_resource(3)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 81)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_004(self):
        #create a project
        source_type = 4
        source = get_resource(4)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_005(self):
        #create a project
        source_type = 5
        source = get_resource(5)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_006(self):
        #create a project
        source_type = 6
        source = get_resource(6)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_007(self):
        #create a project
        source_type = 7
        source = get_resource(7)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 837)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_008(self):
        #create a project
        source_type = 8
        source = get_resource(8)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_009(self):
        #create a project
        source_type = 9
        source = get_resource(9)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)
        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 10)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_010(self):
        #create a project
        source_type = 10
        source = get_resource(10)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        __name__ = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        print("\n", __name__)
        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            print("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            print("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            print("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            print("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
