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
        """Initialize the Librato Connection"""
        assert("LIBRATO_USER" in os.environ and "LIBRATO_TOKEN" in os.environ), \
            "Must set LIBRATO_USER and LIBRATO_TOKEN to run tests"
        cls.conn = librato.connect(os.environ['LIBRATO_USER'], os.environ['LIBRATO_TOKEN'])

    def test_list_metrics(self):
        metrics = self.conn.list_metrics()

    @contextmanager
    def set_sanitizer(self, connection, sanitizer):
        """
        The connection we create does not have a sanitizer.
        For tests involving a sanitizer use this context
        manager to set one and it will ensure that when you are done
        we go back to the default
        """
        original_sanitizer = connection.sanitize
        connection.sanitize = sanitizer
        try:
            yield
        finally:
            self.conn.sanitize = original_sanitizer

    def _add_and_verify_metric(self, name, value, desc, type='gauge', sanitizer=librato.sanitize_no_op):
        with self.set_sanitizer(self.conn, sanitizer):
            self.conn.submit(name, value, type=type, description=desc)
            metric = self.conn.get(name)
            assert metric and metric.name == sanitizer(name)
            assert metric.description == desc
        return metric

    def _delete_and_verify_metric(self, names, sanitizer=librato.sanitize_no_op):
        with self.set_sanitizer(self.conn, sanitizer):
            self.conn.delete(names)
            time.sleep(2)
            # Make sure it's not there anymore
            try:
                metric = self.conn.get(names)
            except:
                metric = None
        assert(metric is None)

    def test_long_sanitized_metric(self):
        name, desc = 'a'*256, 'Too long, will error'
        with self.assertRaises(BadRequest):
            self._add_and_verify_metric(name, 10, desc)
        self._add_and_verify_metric(name, 10, desc, sanitizer=librato.sanitize_metric_name)
        self._delete_and_verify_metric(name, sanitizer=librato.sanitize_metric_name)

    def test_invalid_sanitized_metric(self):
        name, desc = r'I AM #*@#@983221 CRazy((\\\\] invalid', 'Crazy invalid'
        with self.assertRaises(BadRequest):
            self._add_and_verify_metric(name, 10, desc)
        self._add_and_verify_metric(name, 10, desc, sanitizer=librato.sanitize_metric_name)
        self._delete_and_verify_metric(name, sanitizer=librato.sanitize_metric_name)

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

        def run_batch():
            q = self.conn.new_queue()
            q.add(name_one, 10)
            q.add(name_two, 10)
            q.submit()

        with self.assertRaises(BadRequest):
            run_batch()
        with self.set_sanitizer(self.conn, librato.sanitize_metric_name):
            run_batch()

        self.conn.delete([name_one, name_two])

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
        with self.set_sanitizer(self.conn, librato.sanitize_metric_name):
            self.conn.submit(name, 10, description=desc)
            gauge = self.conn.get(name)
            assert gauge.description == desc
        attrs = gauge.attributes['description'] = new_desc
        with self.assertRaises(BadRequest):
            self.conn.update(name, attributes=attrs)
        with self.set_sanitizer(self.conn, librato.sanitize_metric_name):
            self.conn.delete(name)

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

if __name__ == '__main__':
    # TO run a specific test:
    # $ nosetests tests/integration.py:TestLibratoBasic.test_update_metrics_attributes
    nose.runmodule()
