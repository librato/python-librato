import logging
import unittest
import librato
from mock_connection import MockConnect, server

#logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoInstruments(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_alerts_when_none(self):
        ins = self.conn.list_alerts()
        assert len(ins) == 0

if __name__ == '__main__':
    unittest.main()
