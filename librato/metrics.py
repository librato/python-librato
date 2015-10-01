# Copyright (c) 2013. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class Metric(object):
    """Librato Metric Base class"""

    def __init__(self, connection, name, attributes=None, period=None, description=None ):
        self.connection = connection
        self.name = name
        self.attributes = attributes or {}
        self.period = period
        self.description = description
        self.measurements = {}
        self.query = {}
        self.composite = None

    def __getitem__(self, name):
        return self.attributes[name]

    def get(self, name, default=None):
        return self.attributes.get(name, default)

    @classmethod
    def from_dict(cls, connection, data):
        """Returns a metric object from a dictionary item,
        which is usually from librato's API"""
        if data.get('type') == "gauge":
            cls = Gauge
        elif data.get('type') == "counter":
            cls = Counter

        obj = cls(connection, data['name'])
        obj.period = data['period']
        obj.attributes = data['attributes']
        obj.description = data['description'] if 'description' in data else None
        obj.measurements = data['measurements'] if 'measurements' in data else {}
        obj.query = data['query'] if 'query' in data else {}
        obj.composite = data['composite'] if 'composite' in data else None

        return obj

    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self.name)


class Gauge(Metric):
    """Librato Gauge metric"""
    def add(self, value, source=None, **params):
        """Add a new measurement to this gauge"""
        if source:
            params['source'] = source
        return self.connection.submit(self.name, value, type="gauge", **params)

    def what_am_i(self):
        return 'gauges'


class Counter(Metric):
    """Librato Counter metric"""
    def add(self, value, source=None, **params):
        if source:
            params['source'] = source

        return self.connection.submit(self.name, value, type="counter", **params)

    def what_am_i(self):
        return 'counters'
