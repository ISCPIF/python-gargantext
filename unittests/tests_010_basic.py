"""
BASIC UNIT TESTS FOR GARGANTEXT IN DJANGO
=========================================
"""
from django.test import TestCase


class NodeTestCase(TestCase):
    def setUp(self):
        from gargantext.models import nodes
        self.node_1000 = nodes.Node(id=1000)
        self.new_node = nodes.Node()

    def test_010_node_has_id(self):
        '''node_1000.id'''
        self.assertEqual(self.node_1000.id, 1000)

    def test_011_node_write(self):
        '''write new_node to DB and commit'''
        from gargantext.util.db import session
        self.assertFalse(self.new_node._sa_instance_state._attached)
        session.add(self.new_node)
        session.commit()
        self.assertTrue(self.new_node._sa_instance_state._attached)
