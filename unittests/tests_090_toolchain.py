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

    def __get_last_status__(self, Node):
        self.last_status = self._get_statuses(Node)[-1]

    def test_000_create_corpus(self):
        for d in os.listdir(DATA_SAMPLE_DIR):
            print(d)
