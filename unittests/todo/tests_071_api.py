"""
API UNIT TESTS
================
"""
from django.test import TestCase, Client

from gargantext.models import Node
from gargantext.util.db import session

from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

# Using the standard RequestFactory API to create a form POST request
#factory = APIRequestFactory()



class APIRecipe(TestCase):
    def setUp(self):
        """
        Will be run before each test
        """
        self.client = Client()
        # login with our fake user
        response = self.client.post(
                            '/auth/login/',
                            {'username': 'pcorser', 'password': 'peter'}
                            )
        self.create_project()
        self.create_corpus()
        self.factory = APIRequestFactory()


    def create_project(self):

        new_project = Node(
            typename = 'PROJECT',
            name = "My project",
        )
        session.add(new_project)
        session.commit()
        self.project = new_project


    def create_corpus(self):
        #create a default corpus

        self.corpus = self.project.add_child(
            name = "My Corpus",
            typename = 'CORPUS',
        )

        session.add(self.corpus)
        session.commit()


    def test_001_post_project(self):
        '''POST /projects'''
        request = self.factory.post('/api/projects/', {'name': 'PROJECT TEST'}, format='json')

    def test_002_get_projects(self):
        '''GET /projects'''
        request = self.factory.get('/api/projects/', format='json')

    def test_003_put_projects(self):
        '''PUT /projects'''
        request = self.factory.put('/api/projects/', {"name": "My TEST PROJECT"}, format='json')

    def test_004_delete_projects(self):
        '''DELETE /projects'''
        request = self.factory.delete('/api/projects/', format='json')


    def test_005_delete_project(self):
        '''DELETE /project'''
        request = self.factory.delete('/api/project/%s' %self.project.id, format='json')
    def test_006_get_project(self):
        '''GET /PROJECT'''
        request = self.factory.get('/api/project/%s' %self.project.id, format='json')

    def test_007_put_project(self):
        ''' PUT /PROJECT '''
        request = self.factory.put('/api/project/%s' %self.project.id, {"name": "My New Project"}, format='json')
    # def test_008_post_corpus(self):
    #     '''POST /project'''
    #     request = self.factory.post('/project/', {'name': 'PROJECT TEST'})
