import logging
import unittest
from librato import exceptions


class TestErrorMessageParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_request_error(self):
        error_resp = {
          "errors": {
            "request": ["Not found"]
          }
        }
        expected_msg = "request: Not found"
        msg = exceptions.ErrorMessageParser.parse(error_resp)
        self.assertEqual(expected_msg, msg)

    def test_params_error(self):
        error_resp = {
          "errors": {
            "params": {"measure_time": ["too far in past"]}
          }
        }
        expected_msg = "params: measure_time: too far in past"
        msg = exceptions.ErrorMessageParser.parse(error_resp)
        self.assertEqual(expected_msg, msg)

    def test_params_error_multi(self):
        error_resp = {
          "errors": {
            "params": {"name": ["duplicate etc", "bad character etc"]}
          }
        }
        expected_msg = "params: name: duplicate etc, bad character etc"
        msg = exceptions.ErrorMessageParser.parse(error_resp)
        self.assertEqual(expected_msg, msg)

    def test_multiple_params_error(self):
        error_resp = {
          "errors": {
            "params": {
              "measure_time": ["too far in past"],
              "name": ["is not present"]
            }
          }
        }
        expected_msg = "params: measure_time: too far in past, params: name: is not present"
        msg = exceptions.ErrorMessageParser.parse(error_resp)
        self.assertEqual(expected_msg, msg)


if __name__ == '__main__':
    unittest.main()
