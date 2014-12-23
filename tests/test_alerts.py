import logging
import unittest
import librato
from mock_connection import MockConnect, server

# Mock the server
librato.HTTPSConnection = MockConnect


class TestLibratoAlerts(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        self.name = 'my_alert'
        server.clean()

    def test_list_alerts_when_none(self):
        ins = self.conn.list_alerts()
        assert len(ins) == 0

    def test_adding_a_new_alert_without_services_or_conditions(self):
        alert = self.conn.create_alert(self.name)
        assert type(alert) == librato.Alert
        assert alert.name == self.name
        assert alert._id != 0
        assert len(alert.services) == 0
        assert len(alert.conditions) == 0
        assert len(self.conn.list_alerts()) == 1

    def test_adding_a_new_alert_with_a_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('cpu').above(200)
        assert len(alert.services) == 0
        assert len(alert.conditions) == 1
        assert alert.conditions[0].condition_type == 'above'
        assert alert.conditions[0].metric_name == 'cpu'
        assert alert.conditions[0].threshold == 200 

    def test_deleting_an_alert(self):
        alert = self.conn.create_alert(self.name)
        #TODO: use requests directly instead of the client methods?
        assert len(self.conn.list_alerts()) == 1
        self.conn.delete_alert(self.name)
        assert len(self.conn.list_alerts()) == 0
    
    def test_deleting_an_inexistent_alert(self):
        self.conn.create_alert('say_my_name')
        self.conn.delete_alert('say_my_wrong_name')
        assert self.conn.get_alert('say_my_name') is not None
    
    def test_adding_a_new_alert_with_a_service(self):
        alert = self.conn.create_alert(self.name)
        alert.add_service(1)
        assert len(alert.services) == 1
        assert len(alert.conditions) == 0
        assert alert.services[0]._id == 1

    def test_add_above_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('metric_test').above(200, 'average').during(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'above'
        assert condition.metric_name == 'metric_test'
        assert condition.threshold == 200
        assert condition.duration == 5

if __name__ == '__main__':
    unittest.main()
