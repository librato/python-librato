import logging
import unittest
import librato
from mock_connection import MockConnect, server

# logging.basicConfig(level=logging.DEBUG)
# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoAnnotations(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        server.clean()

    def test_get_annotation_stream(self):
        annotation_name = "My_Annotation"
        annotation_stream = self.conn.get_annotation_stream(annotation_name)
        assert type(annotation_stream) == librato.Annotation
        assert annotation_stream.name == annotation_name

    def test_get_payload(self):
        annotation = librato.Annotation(self.conn, 'My_Annotation', 'My_Annotation_Display')
        payload = annotation.get_payload()
        assert payload['name'] == 'My_Annotation'
        assert payload['display_name'] == 'My_Annotation_Display'

    def test_from_dict(self):
        data = {'name': 'My_Annotation', 'display_name': 'My_Annotation_Display', 'query': {}, 'events': {}}
        resp = librato.Annotation.from_dict(self.cls, data)
        assert resp.display_name == 'My_Annotation_Display'
        assert resp.name == 'My_Annotation'
        assert resp.query == {}
        assert resp.events == {}

    def cls(self, connection, data):
        return librato.Annotation(self.conn, '', '')

if __name__ == '__main__':
    unittest.main()
