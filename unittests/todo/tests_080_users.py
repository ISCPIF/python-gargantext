#!/usr/bin/python3 env

from gargantext.util.db import session
from django import TestCase


class UserRecipes(TestCase):
    def setUp(self):
        #before any test
        self.session = session
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
