#!/usr/bin/python3 env
"""
TOOLCHAIN TEST SUITE
"""
#switching to standard testing
from unittest import TestCase
#make http requests
import requests
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# test Nodes
from gargantext.models import Node
from gargantext.constants import RESOURCETYPES, NODETYPES
# provides GargTestRunner.testdb_session
from unittests.framework import GargTestRunner
#API capabilities
#from rest_framework.test import APIRequestFactory




class ToolChainRecipes(TestCase):
    def setUp(self):
        self.session = GargTestRunner.testdb_session
        self.client = Client()
        self.source_list = [(resource["type"], resource["name"]) for resource in RESOURCETYPES]
        self.source_list.insert(0, (0,"Select a database below"))


    def _create_project(self):
        self.project = Node(
            user_id = user.id,
            typename = 'PROJECT',
            name = "test1",
        )
        session.add(self.project)
        session.commit()
        return self.project
    def create_corpus(self, source, name, file):

    def create_test(self):

        type = forms.ChoiceField(
            choices = source_list,
            widget = forms.Select(attrs={ 'onchange' :'CustomForSelect( $("option:selected", this).text() );'})
        )
        name = forms.CharField( label='Name', max_length=199 , widget=forms.TextInput(attrs={ 'required': 'true' }))
        file = forms.FileField()
        def clean_resource(self):
            file_ = self.cleaned_data.get('file')
        def clean_file(self):
            file_ = self.cleaned_data.get('file')
            if len(file_) > 1024 ** 3 : # we don't accept more than 1GB
                raise forms.ValidationError(ugettext_lazy('File too heavy! (>1GB).'))
            return file_







class CoporaRecipes(TestCase):
    def setUp(self):
        self.session = GargTestRunner.testdb_session
        self.client = Client()

class ToolChainRecipes(TestCase):
    def setUp(self):
        # -------------------------------------
        self.session = GargTestRunner.testdb_session
        # -------------------------------------
        self.client = Client()
        #self.user = self.__create_user__()
        #csrf_client = Client(enforce_csrf_checks=True)
    def tearDown(self):
        #del self.user
        del self.session
    #     del self.project
    #     del self.corpus

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

    def test_000_create_user(self):
        self.user.save()
        r = self.client.login(username="john", password="lucyinthesky")
        self.assertEqual(r, True)

    def test_001_authenticate_user(self):
        #/auth/login/
        #self.client(/auth)
        user = authenticate(username='john', password='lucyinthesky')
        self.assertEqual(user.is_active, True)

    def test_002_load_project_template(self):
        response = self.client.get('/projects/')
        print(">>>>>", response)
        print(response.status_code)

    def test_003_get_project_node(self):
        response = self.client.get('/projects/')
        print(">>>>>", response)
        print(response.status_code)


    def test_003_post_project(self):
        response = self.client.post('/projects/', params = {"name": "test1"})
        #print(self.project)
        self.assertEqual(response.status_code, 302)


    def test_004_delete_projects(self):
        response = self.client.delete('/projects/')
        self.assertEqual(response.status_code, 302)
        raise NotImplementedError
    def test_005_put_projects(self):
        params = {"name":"OLD"}
        response = self.client.put('/projects/', params)
        self.assertEqual(response.status_code, 302)
        raise NotImplementedError

    def test_006_add_corpus_form(self):
        project_id = 1
        response = self.client.get('/projects/'+str(project_id))
        #print(response.json())
        raise NotImplementedError
    def test_007_post_corpus(self):
        #response = self.client.post("/projects/"+self.project.id, )
        raise NotImplementedError
