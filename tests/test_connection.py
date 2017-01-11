import logging
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import librato
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestConnection(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test', tags={'sky': 'blue'})
        server.clean()

    def test_constructor_tags(self):
        tags = self.conn.get_tags()
        assert len(tags) == 1
        assert 'sky' in tags
        assert tags['sky'] == 'blue'

    def test_add_tags(self):
        self.conn.add_tags({'sky': 'red', 'coal': 'black'})
        tags = self.conn.get_tags()

        assert len(tags) == 2
        assert 'sky' in tags
        assert tags['sky'] == 'red'

        assert 'coal' in tags
        assert tags['coal'] == 'black'

    def test_set_tags(self):
        self.conn.set_tags({'coal': 'black'})
        tags = self.conn.get_tags()

        assert len(tags) == 1
        assert 'coal' in tags
        assert tags['coal'] == 'black'

    def test_custom_ua(self):
        self.conn.custom_ua = 'foo'
        assert self.conn._compute_ua() == 'foo'

if __name__ == '__main__':
    unittest.main()
