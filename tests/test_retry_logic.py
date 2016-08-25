import logging
import unittest
import librato
import mock_connection

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = mock_connection.MockConnect


class TestRetries(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        mock_connection.server.clean()

    def test_list_metrics_with_retries(self):
        self.conn.fake_n_errors = 1
        self.conn.backoff_logic = lambda x: 0.1  # We don't want to wait 1 sec for this to finish
        metrics = self.conn.list_metrics()
        assert len(metrics) == 0

if __name__ == '__main__':
    unittest.main()
