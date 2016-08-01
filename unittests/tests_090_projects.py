#!/usr/bin/python3 env
class ProjectsRecipes(TestCase):
    def setUp(self):
        #before anytest
        self.session = GargTestRunner.testdb_session
        self.client = Client()

    def tearDown(self):
        #after any test
        pass

    def _create_projet(self):
        #resp = self.client.post('/projects/', data={"name":"test"})
        self.project = Node(
            user_id = user.id,
            typename = 'PROJECT',
            name = "test1",
        )
        session.add(self.project)
        session.commit()
        return self.project


    def test_001_get_projects(self):
        '''get every projects'''
        resp = self.client.get('/projects/')
        self.assertEqual(resp.status_code, 200)

    def test_002_delete_projects(self):
        '''delete every projects'''
        resp = self.client.delete('/projects/')
        self.assertEqual(resp.status_code, 204)

    def test_003_put_projects(self):
        '''modify every projects'''
        resp = self.client.put('/projects?name="test"')
        self.assertEqual(resp.status_code, 202)

    def test_004_post_project(self):
        '''create a project'''
        resp = self.client.post('/projects/', data={"name":"test"})
        self.assertEqual(resp.status_code, 201)

    def test_005_get_project(self):
        '''get one project'''
        project = self._create_projet()
        resp = self.client.delete('/project/'+project.id)
        self.assertEqual(resp.status_code, 200)

    def test_006_delete_project(self):
        '''delete one project'''
        project = self._create_projet()
        #delete it
        resp = self.client.delete('/project/'+project.id)
        self.assertEqual(resp.status_code, 204)

    def test_007_put_project(self):
        project = self._create_projet()
        resp = self.client.put('/project/'+project.id+"?name=newname")
        self.assertEqual(resp.status_code, 204)
        pass
