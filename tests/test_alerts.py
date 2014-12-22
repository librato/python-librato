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

    def test_adding_a_new_alert_without_services_or_conditions(self):
        name = "my_alert"
        alert = self.conn.create_alert(name)
        assert type(alert) == librato.Alert
        assert alert.name == name
        assert alert._id != 0
        assert len(alert.services) == 0
        assert len(alert.conditions) == 0
        assert len(self.conn.list_alerts()) == 1

    def test_adding_a_new_alert_with_one_condition(self):
        name = "my_alert"
        alert = self.conn.create_alert(name)
        alert.add_condition('above', 200, "metric_test")
        assert alert.name == name
        assert len(alert.services) == 0
        assert len(alert.conditions) == 1
        assert alert.conditions[0].condition_type == 'above'
        assert alert.conditions[0].metric_name == 'metric_test'
        assert alert.conditions[0].threshold == 200 

    def test_deleting_an_alert(self):
        name = "my_alert"
        alert = self.conn.create_alert(name)
        #TODO: use requests directly instead of the client methods?
        assert len(self.conn.list_alerts()) == 1
        logging.info(alert._id)
        logging.info(type(alert._id))
        self.conn.delete_alert(alert._id)
        assert len(self.conn.list_alerts()) == 0

if __name__ == '__main__':
    unittest.main()
