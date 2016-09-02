"""
ROUTE UNIT TESTS
================
"""
from django.test import TestCase
from django.test import Client

# to be able to create Nodes
from gargantext.models import Node

# to be able to compare in test_073_get_api_one_node()
from gargantext.constants import NODETYPES

from gargantext.util.db   import session

class RoutesChecker(TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Will be run *once* for all tests here

        NEEDS TO HAVE TestCase.setUpClass()
        """
        TestCase.setUpClass()
        new_project = Node(
            typename = 'PROJECT',
            name = "hello i'm a project",
            user_id = 1                   # todo make sure it's the same user as login
        )
        session.add(new_project)
        session.commit()
        cls.a_node_id = new_project.id
        print("created a project with id: %i" % new_project.id)

    def setUp(self):
        """
        Will be run before *each* test here
        """
        self.client = Client()

        # login with our fake user
        response = self.client.post(
                            '/auth/login/',
                            {'username': 'pcorser', 'password': 'peter'}
                            )
        # print(response.status_code) # expected: 302 FOUND

    def test_071a_get_front_page(self):
        ''' get the front page / '''
        front_response = self.client.get('/')
        self.assertEqual(front_response.status_code, 200)
        self.assertIn('text/html', front_response.get('Content-Type'))
        # on suppose que la page contiendra toujours ce titre
        self.assertIn(b'<h1>Gargantext</h1>', front_response.content)

    def test_071b_get_inexisting_page(self):
        ''' get the inexisting page /foo '''
        front_response = self.client.get('/foo')
        self.assertEqual(front_response.status_code, 404)

    def test_072_get_api_nodes(self):
        ''' get "/api/nodes" '''
        api_response = self.client.get('/api/nodes')
        self.assertEqual(api_response.status_code, 200)

        # 1) check the type is json
        self.assertTrue(api_response.has_header('Content-Type'))
        self.assertIn('application/json', api_response.get('Content-Type'))

        # 2) let's try to get things in the json
        json_content = api_response.json()
        print(json_content)
        json_count = json_content['count']
        json_nodes = json_content['records']
        self.assertEqual(type(json_count), int)
        self.assertEqual(type(json_nodes), list)

    def test_073_get_api_one_node(self):
        ''' get "api/nodes/<node_id>" '''
        one_node_route = '/api/nodes/%i' % RoutesChecker.a_node_id
        # print("\ntesting node route: %s" % one_node_route)
        api_response = self.client.get(one_node_route)
        self.assertTrue(api_response.has_header('Content-Type'))
        self.assertIn('application/json', api_response.get('Content-Type'))

        json_content = api_response.json()
        nodetype = json_content['typename']
        nodename = json_content['name']
        print("\ntesting nodename:", nodename)
        print("\ntesting nodetype:", nodetype)
        self.assertIn(nodetype, NODETYPES)
        self.assertEqual(nodename, "hello i'm a project")

    # TODO http://localhost:8000/api/nodes?types[]=CORPUS

    # £TODO test request.*
        # print ("request")
        # print ("user.id", request.user.id)
        # print ("user.name", request.user.username)
        # print ("path", request.path)
        # print ("path_info", request.path_info)
