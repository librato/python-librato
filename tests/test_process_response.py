import logging
import unittest
try:
    from unittest.mock import create_autospec, PropertyMock
except ImportError:
    from mock import create_autospec, PropertyMock
import librato
from mock_connection import MockConnect, server
from six.moves.http_client import HTTPResponse

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibrato(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_get_authentication_failure(self):
        """
        fails with Unauthorized on 401 during GET
        """
        mock_response = create_autospec(HTTPResponse, spec_set=True, instance=True)
        mock_response.mock_add_spec(['status'], spec_set=True)
        mock_response.status = 401
        # GET 401 responds with JSON
        mock_response.getheader.return_value = "application/json;charset=utf-8"
        mock_response.read.return_value = '{"errors":{"request":["Authorization Required"]}}'.encode('utf-8')

        with self.assertRaises(librato.exceptions.Unauthorized):
            self.conn._process_response(mock_response, 1)

    def test_post_authentication_failure(self):
        """
        fails with Unauthorized on 401 during POST
        """
        mock_response = create_autospec(HTTPResponse, spec_set=True, instance=True)
        mock_response.mock_add_spec(['status'], spec_set=True)
        mock_response.status = 401
        # POST 401 responds with text
        mock_response.getheader.return_value = "text/plain"
        mock_response.read.return_value = 'Credentials are required to access this resource.'.encode('utf-8')

        with self.assertRaises(librato.exceptions.Unauthorized):
            self.conn._process_response(mock_response, 1)
