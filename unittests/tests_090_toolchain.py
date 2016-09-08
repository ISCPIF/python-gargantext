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

from gargantext.util.toolchain.main import *
DATA_SAMPLE_DIR = "/srv/gargantext/unittests/mini_test_samples/"

# todo make it read NDOCS from a json overview to add in DATA_SAMPLE_DIR
DATA_SAMPLE_NDOCS = [
                        None,     # RESOURCETYPES
                         [7],     #  1-europresse
                          [],     #  2-jstor
                        [10],     #  3-pubmed
                          [],     #  4-scopus
                          [],     #  5-web_of_science
                        [12],     #  6-zotero
                          [],     #  7-csv
                        [32],     #  8-istex
                          [],     #  9-scoap
                          [],     # 10-repec
                    ]


class ToolChainRecipes(TestCase):

    def setUp(self):
        #self.session = GargTestRunner.testdb_session
        self.session = session
        self.log= logging.getLogger( "unitests.test_090_toolchain" )
        self.client = Client()
        self.user = User()
        self.project = self._create_project()
        self.source_list = [(resource["type"], resource["name"]) for resource in RESOURCETYPES]
        self.source_list.insert(0, (0,"Select a database below"))
        self.sample_files = self._collect_samples_files()

    def _create_project(self):
        project = Node(
            user_id = self.user.id,
            typename = 'PROJECT',
            name = "test1000",
        )
        self.session.add(project)
        self.session.commit()
        return project

    def __count_node_children__(self, CurrNode, typename=None):
        '''count ALL the children of a given Node [optional filter TYPENAME] '''
        if typename is None:
            children = CurrNode.children('').count()
        else:
            children = CurrNode.children(typename).count()
        return children

    def __find_node_parent__(self, CurrNode):
        '''find the parent Node given a CurrNode '''
        self.parent = self.session.query(Node).filter(Node.id == CurrNode.parent_id).first()

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
            if not isfile(full_path):
                if format_source in sources:
                    self.sample_files[format_source] = [join(full_path, samplef) for samplef in os.listdir(full_path)]
        return self.sample_files

    def _create_corpus(self,name, source_type, sample_file):
        corpus = self.project.add_child(
            name = name,
            typename = 'CORPUS',
        )
        corpus.add_resource(
            type = int(source_type),
            path = sample_file,
        )
        self.session.add(corpus)
        self.session.commit()
        return corpus

    def _get_corpus(self, name):
        corpus = self.session.query(Node).filter(Node.typename == "CORPUS", Node.name == name).first()
        return corpus

    def _run_recipe(self, source_type, expected_results):
        """
        Each of the resources input test can follow this common recipe base

        @param source_type:          int   (cf. constants.py RESOURCETYPES)
        @param expected_results:    int[]   (number of docs for each sample corpora of this source)
        """
        source = get_resource(source_type)
        source_name = source["name"].split("[")[0].lower().strip().replace(" ", "_")

        self.test_name = ">>  "+ sys._getframe().f_code.co_name +"_"+str(source_name)+":"
        self.log.debug("\n" + self.test_name)

        for i,sample_file in enumerate(self.sample_files[source_name]):
            print("... sample_file:", sample_file)
            expected_ndocs = expected_results[i]
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
            real_ndocs = self.__count_node_children__(self.corpus, "DOCUMENT")
            # print('==>\t'+str(source_type)+'\t'+str(i)+'\t'+sample_file+'\t'+str(real_ndocs))
            self.assertEqual(real_ndocs, expected_ndocs)
            status = self.corpus.status()
            self.log.debug("\t- Extracting ngrams")
            extract_ngrams(self.corpus)
            # ngrams = self.__count_node_children__(self.corpus, "NGRAMS")
            status = self.corpus.status()
            self.assertTrue(status["complete"])

    def test_000_get_project(self):
        self.client.get("/projects/%i" %self.project.id)

    def tests_001_europresse(self):
        '''testing Europresse parsing'''
        self._run_recipe(1, DATA_SAMPLE_NDOCS[1])

    # def tests_002_jstor(self):
    #     self._run_recipe(2, DATA_SAMPLE_NDOCS[2])

    def tests_003_pubmed(self):
        self._run_recipe(3, DATA_SAMPLE_NDOCS[3])

    # def tests_004_scopus(self):
    #     self._run_recipe(4, DATA_SAMPLE_NDOCS[4])
    #
    # def tests_005_web_of_science(self):
    #     self._run_recipe(5, DATA_SAMPLE_NDOCS[5])

    def tests_006_zotero(self):
        self._run_recipe(6, DATA_SAMPLE_NDOCS[6])

    # def tests_007_csv(self):
    #     self._run_recipe(7, DATA_SAMPLE_NDOCS[7])

    def tests_008_istex(self):
        self._run_recipe(8, DATA_SAMPLE_NDOCS[8])

    # def tests_009_scoap(self):
    #     self._run_recipe(9, DATA_SAMPLE_NDOCS[9])
    #
    # def tests_010_repec(self):
    #     self._run_recipe(10, DATA_SAMPLE_NDOCS[10])
