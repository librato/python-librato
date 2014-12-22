# Copyright (c) 2012 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging
from contextlib import contextmanager
import unittest
from librato.exceptions import BadRequest
import librato
import os
from random import randint
import time
logging.basicConfig(level=logging.INFO)


class TestLibratoBasic(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        user = os.environ.get('LIBRATO_USER')
        token = os.environ.get('LIBRATO_TOKEN')
        """Initialize the Librato Connection"""
        assert user and token, "Must set LIBRATO_USER and LIBRATO_TOKEN to run tests"
        cls.conn = librato.connect(user, token)
        cls.conn_sanitize = librato.connect(user, token, sanitizer=librato.sanitize_metric_name)

    def test_list_metrics(self):
        metrics = self.conn.list_metrics()

    def _add_and_verify_metric(self, name, value, desc, connection=None, type='gauge'):
        if not connection:
            connection = self.conn
        connection.submit(name, value, type=type, description=desc)
        metric = connection.get(name)
        assert metric and metric.name == connection.sanitize(name)
        assert metric.description == desc
        return metric

    def _delete_and_verify_metric(self, names, connection=None):
        if not connection:
            connection = self.conn
        connection.delete(names)
        time.sleep(2)
        # Make sure it's not there anymore
        try:
            metric = connection.get(names)
        except:
            metric = None
        assert(metric is None)

    def test_long_sanitized_metric(self):
        name, desc = 'a'*256, 'Too long, will error'
        with self.assertRaises(BadRequest):
            self._add_and_verify_metric(name, 10, desc, self.conn)
        self._add_and_verify_metric(name, 10, desc, self.conn_sanitize)
        self._delete_and_verify_metric(name, self.conn_sanitize)

    def test_invalid_sanitized_metric(self):
        name, desc = r'I AM #*@#@983221 CRazy((\\\\] invalid', 'Crazy invalid'
        with self.assertRaises(BadRequest):
            self._add_and_verify_metric(name, 10, desc, self.conn)
        self._add_and_verify_metric(name, 10, desc, self.conn_sanitize)
        self._delete_and_verify_metric(name, self.conn_sanitize)

    def test_create_and_delete_gauge(self):
        name, desc = 'Test', 'Test Gauge to be removed'
        self._add_and_verify_metric(name, 10, desc)
        self._delete_and_verify_metric(name)

    def test_create_and_delete_counter(self):
        name, desc = 'Test_counter', 'Test Counter to be removed'
        self._add_and_verify_metric(name, 10, desc, type='counter')
        self._delete_and_verify_metric(name)

    def test_batch_delete(self):
        name_one, desc_one = 'Test_one', 'Test gauge to be removed'
        name_two, desc_two = 'Test_two', 'Test counter to be removed'
        self._add_and_verify_metric(name_one, 10, desc_one)
        self._add_and_verify_metric(name_two, 10, desc_two, type='counter')
        self._delete_and_verify_metric([name_one, name_two])

    def test_save_gauge_metrics(self):
        name, desc = 'Test', 'Test Counter to be removed'
        self.conn.submit(name, 10, description=desc)
        self.conn.submit(name, 20, description=desc)
        self.conn.delete(name)

    def test_send_batch_gauge_measurements(self):
        q = self.conn.new_queue()
        for t in range(1, 10):
            q.add('temperature', randint(20, 40))
        q.submit()

        for t in range(1, 10):
            q.add('temperature', randint(20, 40), measure_time=time.time()+t)
        q.submit()

        for t in range(1, 10):
            q.add('temperature', randint(20, 40), source='upstairs', measure_time=time.time()+t)
        q.submit()

        for t in range(1, 50):
            q.add('temperature', randint(20, 30), source='downstairs', measure_time=time.time()+t)
        q.submit()
        self.conn.delete('temperature')

    def test_batch_sanitation(self):
        name_one, name_two = 'a'*500, r'DSJAK#32102391S,m][][[{{]\\'

        def run_batch(connection):
            q = connection.new_queue()
            q.add(name_one, 10)
            q.add(name_two, 10)
            q.submit()

        with self.assertRaises(BadRequest):
            run_batch(self.conn)
        run_batch(self.conn_sanitize)

        self.conn_sanitize.delete([name_one, name_two])

    def test_submit_empty_queue(self):
        self.conn.new_queue().submit()

    def test_send_batch_counter_measurements(self):
        q = self.conn.new_queue()
        for nr in range(1, 2):
            q.add('num_req', nr, type='counter', source='server1', measure_time=time.time()-1)
            q.add('num_req', nr, type='counter', source='server2', measure_time=time.time()-1)
        q.submit()

    def test_update_metrics_attributes(self):
        name, desc = 'Test', 'A great gauge.'
        self.conn.submit(name, 10, description=desc)
        gauge = self.conn.get(name)
        assert gauge and gauge.name == name
        assert gauge.description == desc

        gauge = self.conn.get(name)
        attrs = gauge.attributes
        attrs['display_min'] = 0
        self.conn.update(name, attributes=attrs)

        gauge = self.conn.get(name)
        assert gauge.attributes['display_min'] == 0

        self.conn.delete(name)

    def test_sanitized_update(self):
        name, desc = 'a'*1000, 'too long, really'
        new_desc = 'different'
        self.conn_sanitize.submit(name, 10, description=desc)
        gauge = self.conn_sanitize.get(name)
        assert gauge.description == desc

        attrs = gauge.attributes['description'] = new_desc
        with self.assertRaises(BadRequest):
            self.conn.update(name, attributes=attrs)
        self.conn_sanitize.delete(name)

    def test_instruments(self):
        _c = self.conn

        _c.submit("server_temp", value="23", source="app1")
        _c.submit("environmental_temp", value="18", source="rack1")

        _c.create_instrument("Server Temperature",
            streams = [
                        { "metric": "server_temp", "source":"app1" },
                        { "metric": "environmental_temp", "source":"rack1" }
                      ],
            attributes = { "display_integral": True} )


        """
        dbs = _c.list_dashboards()
        assert len(dbs) > 0

        _c.create_dashboard("foo_", instruments = [ { "id": 1 }, { "id": 2 } ] )
        """
    
    def test_alerts(self):
        alerts = self.conn.list_alerts()
    
    def test_add_empty_alert(self):
        name = "test_add_empty_alert" + str(time.time())
        alert = self.conn.create_alert(name)
        alerts = self.conn.list_alerts()
        result = [a for a in alerts if a._id == alert._id]
        assert len(result) == 1
        assert result[0]._id == alert._id
        assert result[0].name == alert.name
        assert len(result[0].conditions) == 0
        assert len(result[0].services) == 0

    def test_add_alert_with_one_condition(self):
        name = "test_add_alert_with_one_condition" + str(time.time())
        alert = self.conn.create_alert(name)
        alert.add_condition('above', 200, "metric_test")
        alert.save()
        alerts = self.conn.list_alerts()
        result = [a for a in alerts if a._id == alert._id]
        assert len(result) == 1
        assert len(result[0].conditions) == 1
        assert result[0].conditions[0].condition_type == 'above'
        assert result[0].conditions[0].metric_name == 'metric_test'

    def test_delete_alert(self):
        name = "test_delete_alert" + str(time.time())
        alert = self.conn.create_alert(name)
        alert_id = alert._id
        alert = self.conn.get_alert(alert_id)
        assert alert.name == name
        self.conn.delete_alert(alert._id)
        time.sleep(2)
        # Make sure it's not there anymore
        try:
            alert = connection.get(names)
        except:
            alert = None
        assert(alert is None)

    def test_adding_a_new_instrument_with_composite_metric_stream(self):
        name = "my_INST_with_STREAMS"
        ins = self.conn.create_instrument(name)
        ins_id = ins.id
        ins.new_stream(composite='s("cpu", "*")')
        self.conn.update_instrument(ins)
        ins = self.conn.get_instrument(ins.id)
        assert ins.name == name
        assert ins.id == ins_id
        assert len(ins.streams) == 1
        assert ins.streams[0].composite == 's("cpu", "*")'

    def test_instrument_save_creates_new_record(self):
        instrument_name = 'my instrument name'
        i = librato.Instrument(self.conn, instrument_name)
        assert i.id is None
        i.save()
        assert i.name == instrument_name

    def test_instrument_save_updates_existing_record(self):
        instrument_name = 'my instrument name'
        i = self.conn.create_instrument(instrument_name)
        assert i.name == instrument_name
        i.name = 'NEW instrument name'
        i.save()
        i = self.conn.get_instrument(i.id)
        assert i.name == 'NEW instrument name'

if __name__ == '__main__':
    # TO run a specific test:
    # $ nosetests tests/integration.py:TestLibratoBasic.test_update_metrics_attributes
    nose.runmodule()
