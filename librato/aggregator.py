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


class Aggregator(object):
    """ Implements client-side aggregation to reduce the number of measurements
    submitted.  Specify a period (default: 60) and the aggregator will automatically
    floor the measure_times to that interval.
    """

    def __init__(self, connection, source=None):
        self.connection = connection
        self.source = source
        self.measurements = {}
        self.period = 60

    def add(self, name, value):
        if name not in self.measurements:
            self.measurements[name] = {
                #'value': value,
                'count': 1, 'sum': value, 'min': value, 'max': value
                }
        else:
            m = self.measurements[name]
            m['sum'] += value
            m['count'] += 1
            #m['value'] = float(m['sum']) / float(m['count'])
            if value < m['min']:
                m['min'] = value
            if value > m['max']:
                m['max'] = value

        return self.measurements

    def to_payload(self):
        # Remove the 'value' field or API will throw an error
        # 'value' will be calculated at the API
        #for name in self.measurements:
        #    # TODO: make a clone so we can delete that instead
        #    v = self.measurements[name].get('value')
        #    if v:
        #        del(self.measurements[name]['value'])
        body = []
        for m in self.measurements:
            h = self.measurements[m]
            h['name'] = m
            body.append(h)

        result = {'gauges': body}
        if self.source:
            result['source'] = self.source
        return result

    def clear(self):
        self.measurements = {}

    def submit(self):
        self.connection._mexe("metrics",
                method="POST",
                query_props=self.to_payload())


