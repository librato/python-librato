import logging
import unittest
import librato


class TestLibratoUrlEncoding(unittest.TestCase):

    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')

    def test_string_encoding(self):
        params = {"name": "abcd"}
        assert self.conn._url_encode_params(params) == 'name=abcd'

    def test_list_encoding(self):
        params = {"sources": ['a', 'b']}
        assert self.conn._url_encode_params(params) == 'sources%5B%5D=a&sources%5B%5D=b'

    def test_empty_encoding(self):
        params = {}
        assert self.conn._url_encode_params(params) == ''

if __name__ == '__main__':
    unittest.main()
