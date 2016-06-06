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
    
    def test_adding_an_alert_with_description(self):
        alert = self.conn.create_alert(self.name, description="test_description")
        assert alert.description == "test_description"

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
        alert.add_condition_for('metric_test').above(200, 'average').duration(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'above'
        assert condition.metric_name == 'metric_test'
        assert condition.threshold == 200
        assert condition._duration == 5

    def test_add_below_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('metric_test').below(200, 'average').duration(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'below'
        assert condition.metric_name == 'metric_test'
        assert condition.threshold == 200
        assert condition._duration == 5

    def test_add_absent_condition(self):
        alert = self.conn.create_alert(self.name)
        alert.add_condition_for('metric_test').stops_reporting_for(5)
        assert len(alert.conditions) == 1
        condition = alert.conditions[0]
        assert condition.condition_type == 'absent'
        assert condition.metric_name == 'metric_test'
        assert condition._duration == 5

    def test_immediate_condition(self):
        cond = librato.alerts.Condition('foo')

        cond._duration = None
        assert cond.immediate() == True

        # Not even sure this is a valid case, but testing anyway
        cond._duration = 0
        assert cond.immediate() == True

        cond._duration = 60
        assert cond.immediate() == False

class TestService(unittest.TestCase):
    def setUp(self):
        self.conn = librato.connect('user_test', 'key_test')
        self.sample_payload = {
            'title': 'Email Ops',
            'type': 'mail',
            'settings': {'addresses': 'someone@example.com'}
        }
        server.clean()

    def test_list_services(self):
        services = self.conn.list_services()
        self.assertEqual(len(services), 0)
        # Hack this into the server until we have a :create_service
        # method on the actual connection
        server.create_service(self.sample_payload)
        # id is 1
        self.assertEqual(server.services[1], self.sample_payload)
        services = self.conn.list_services()
        self.assertEqual(len(services), 1)
        s = services[0]
        self.assertIsInstance(s, librato.alerts.Service)
        self.assertEqual(s.title, self.sample_payload['title'])
        self.assertEqual(s.type, self.sample_payload['type'])
        self.assertEqual(s.settings, self.sample_payload['settings'])

    def test_init_service(self):
        s = librato.alerts.Service(123, title='the title', type='mail',
                settings={'addresses': 'someone@example.com'})
        self.assertEqual(s._id, 123)
        self.assertEqual(s.title, 'the title')
        self.assertEqual(s.type, 'mail')
        self.assertEqual(s.settings['addresses'], 'someone@example.com')

    def test_service_from_dict(self):
        payload = {'id': 123, 'title': 'the title', 'type': 'slack',
            'settings': {'room': 'a room'}}
        s = librato.alerts.Service.from_dict(self.conn, payload)
        self.assertEqual(s._id, 123)
        self.assertEqual(s.title, payload['title'])
        self.assertEqual(s.type, payload['type'])
        self.assertEqual(s.settings['room'], payload['settings']['room'])


if __name__ == '__main__':
    unittest.main()
