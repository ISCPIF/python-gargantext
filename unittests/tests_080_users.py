#!/usr/bin/python3 env
# provides GargTestRunner.testdb_session
from unittests.framework import GargTestRunner
from Django import TestCase

class UserRecipes(TestCase):
    def setUp(self):
        #before any test
        self.session = GargTestRunner.testdb_session
        self.client = Client()
    def tearDown(self):
        #after any test
        pass
    def test_000_create_user(self):
        pass
    def test_001_login(self):
        pass
    def test_002_authenticate(self):
        pass
    def test_003_unlogin(self):
        pass
