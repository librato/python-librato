import logging
import unittest
from librato import exceptions


class TestClientError(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        ex = exceptions.ClientError(123, "Bad request etc")
        self.assertIsInstance(ex, Exception)
        self.assertEqual(123, ex.code)
        # Sets message on Exception
        self.assertEqual(str(ex), ex.error_message())

    def test_parse_error_message_standard(self):
        ex = exceptions.ClientError(400, "a standard message")
        self.assertEqual("a standard message", ex._parse_error_message())

    def test_parse_error_message_request_scalar(self):
        error_resp = {
            "errors": {
                "request": "test error message"
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        self.assertEqual("request: test error message", ex._parse_error_message())

    def test_parse_error_message_request(self):
        error_resp = {
            "errors": {
                "request": ["Not found"]
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        self.assertEqual("request: Not found", ex._parse_error_message())

    def test_parse_error_message_request_multiple(self):
        error_resp = {
            "errors": {
                "request": ["Not found", "Another error"]
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        self.assertEqual("request: Not found, request: Another error", ex._parse_error_message())

    def test_parse_error_message_params(self):
        error_resp = {
            "errors": {
                "params": {"measure_time": ["too far in past"]}
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        self.assertEqual("params: measure_time: too far in past", ex._parse_error_message())

    def test_parse_error_message_params_multi_message(self):
        error_resp = {
            "errors": {
                "params": {"name": ["duplicate etc", "bad character etc"]}
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        self.assertEqual("params: name: duplicate etc, bad character etc", ex._parse_error_message())

    def test_parse_error_message_params_multiple(self):
        error_resp = {
            "errors": {
                "params": {
                    "measure_time": ["too far in past"],
                    "name": "mymetricname"
                }
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        msg = ex._parse_error_message()
        self.assertRegexpMatches(msg, "params: measure_time: too far in past")
        self.assertRegexpMatches(msg, "params: name: mymetricname")

    def test_parse_error_message_params_multiple_2nd_level(self):
        error_resp = {
            "errors": {
                "params": {
                    "conditions": {
                        "duration": ["must be set"]
                    }
                }
            }
        }
        ex = exceptions.ClientError(400, error_resp)
        msg = ex._parse_error_message()
        self.assertEqual(msg, 'params: conditions: duration: must be set')

    def test_error_message(self):
        ex = exceptions.ClientError(400, "Standard message")
        self.assertEqual("[400] Standard message", ex.error_message())
        ex = exceptions.ClientError(400, {"errors": {"request": ["Not found"]}})
        self.assertEqual("[400] request: Not found", ex.error_message())

    def test_error_vs_errors(self):
        msg = "You have hit the rate limit, etc"
        # The API actually returns 'errors' in most cases, but for rate
        # limiting we get 'error' (singular)
        error_resp = {'request_time': 1467306906, 'error': msg}
        ex = exceptions.ClientError(403, error_resp)
        parsed_msg = ex._parse_error_message()
        self.assertEqual(msg, parsed_msg)


if __name__ == '__main__':
    unittest.main()
