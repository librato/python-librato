import logging
import unittest
import librato
from mock_connection import MockConnect, server

logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect

class TestLibrato(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_list_instruments_when_none(self):
        ins = self.conn.list_instruments()
        assert len(ins) == 0

    def test_adding_a_new_instrument_without_streams(self):
        ins = self.conn.create_instrument("my_INST")
        assert 1 == 1

if __name__ == '__main__':
    unittest.main()
