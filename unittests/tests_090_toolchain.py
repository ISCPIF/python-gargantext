#!/usr/bin/python3 env
"""
STORY TEST SUITE
testing toolchain
"""
import os, sys, logging
from django.test import TestCase, Client, RequestFactory
from gargantext.models import Node, User
from gargantext.util.db import session


from gargantext.constants import RESOURCETYPES, NODETYPES, get_resource
# provides GargTestRunner.testdb_session
#from unittests.framework import GargTestRunner

from gargantext.util.toolchain.main import *
DATA_SAMPLE_DIR = "/srv/gargantext_lib/data_samples/"

class ToolChainRecipes(TestCase):

    def setUp(self):
        #self.session = GargTestRunner.testdb_session
        self.session = session
        self.log= logging.getLogger( "SomeTest.testSomething" )
        self.client = Client()
        self.user = User()
        self.project = self._create_project()
        self.source_list = [(resource["type"], resource["name"]) for resource in RESOURCETYPES]
        self.source_list.insert(0, (0,"Select a database below"))
        self.sample_files = self._collect_samples_files()

    def tearDown(self):
        #del self.session
        del self.client
        #del self.factory
        del self.source_list
        del self.sample_files
        del self.project

    def _create_project(self):
        self.project = Node(
            user_id = self.user.id,
            typename = 'PROJECT',
            name = "test1000",
        )
        self.session.add(self.project)
        self.session.commit()
        return self.project



    def __count_node_children__(self, CurrNode, typename=None):
        '''find ALL the children of a given Node [optionnal filter TYPENAME] '''
        if typename is None:
            self.children = CurrNode.children('', order=True).count()
        else:
            self.children = CurrNode.children(typename, order=True).count()
        return self.children
    def __find_node_parent__(self, CurrNode):
        '''find the parent Node given a CurrNode '''
        self.parent = self.session.query(Node).filter(Node.id == Node.parent_id, Node.name == name).first()

    def _collect_samples_files(self):
        from collections import defaultdict
        from os.path import isfile, join
        self.sample_files = {}
        sources = [ r["name"].split("[")[0].lower().strip() for r in RESOURCETYPES]
        sources = [r.replace(" ", "_") for r in sources]
        #self.log.debug(sources)
        for format_source in os.listdir(DATA_SAMPLE_DIR):
            #self.log.debug(format_source)
            full_path = join(DATA_SAMPLE_DIR, format_source)
            if not os.path.isfile(full_path):
                if format_source in sources:
                    self.sample_files[format_source] = [join(full_path, samplef) for samplef in os.listdir(full_path)]
        return self.sample_files
    def _create_corpus(self,name, source_type, sample_file):
        self.corpus = self.project.add_child(
            name = name,
            typename = 'CORPUS',
        )
        self.corpus.add_resource(
            type = int(source_type),
            path = sample_file,
        )
        self.session.add(self.corpus)
        self.session.commit()
        return self.corpus
    def _get_corpus(self, name):
        corpus = self.session.query(Node).filter(Node.typename == "CORPUS", Node.name == name).first()
        return corpus
    def test_000_post(self):
        self.client.get("/projects/%i" %self.project.id)

    def tests_001_europresse(self):
        '''testing Europresse parsing'''
        #create a project
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +":"
        print("tests_001_europresse, name:", self.test_name)
        self.log.debug("\n" + self.test_name)

        source_type = 1

        for i,sample_file in enumerate(self.sample_files["europresse"]):
            name = "testEuropress_"+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 4)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])

    def tests_002(self):
        #create a project
        source_type = 2
        source = get_resource(2)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")

        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)


        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_003(self):
        #create a project
        source_type = 3
        source = get_resource(3)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 81)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_004(self):
        #create a project
        source_type = 4
        source = get_resource(4)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_005(self):
        #create a project
        source_type = 5
        source = get_resource(5)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_006(self):
        #create a project
        source_type = 6
        source = get_resource(6)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_007(self):
        #create a project
        source_type = 7
        source = get_resource(7)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 837)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_008(self):
        #create a project
        source_type = 8
        source = get_resource(8)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)



        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_009(self):
        #create a project
        source_type = 9
        source = get_resource(9)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)
        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 10)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])
    def tests_010(self):
        #create a project
        source_type = 10
        source = get_resource(10)
        self.log.debug(source)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")
        self.log.debug(source_name)
        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)
        for i,sample_file in enumerate(self.sample_files[source_name]):
            name = "test_"+source_name+str(i)
            self.log.debug("\t- Checking creation of corpus %s" %name)
            self.corpus = self._create_corpus(name, source_type, sample_file)
            db_corpus = self._get_corpus(name)
            #corpus check

            self.assertEqual(self.corpus.name, db_corpus.name)
            self.log.debug("\t- Checking creation of resource type '%s' " %get_resource(source_type)["name"])
            self.assertEqual(self.corpus.resources()[0]["type"], db_corpus.resources()[0]["type"])
            self.log.debug("\t- Parsing and indexing corpus")
            parse(self.corpus)
            docs = self.__count_node_children__(self.corpus, "DOCUMENT")
            self.assertEqual(docs, 50)
            status = self.corpus.status()
            self.assertTrue(status["complete"])
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "unitests.test_090_toolchain" ).setLevel( logging.DEBUG )
    unittest.main()
