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

class CompositeMetric(object):
    def __init__(self, connection, **params):
        self.connection = connection
        self.measurements = {}
        self.query = {}
        self.compose = params.get('compose')
        self.resolution = params.get('resolution', 60)
        self.start_time = params.get('start_time')
        self.end_time = params.get('end_time')

    def query_params(self):
        params = {
              'resolution': self.resolution,
              'start_time': self.start_time
              }
        if self.end_time:
            params['end_time'] = self.end_time
        return params

    # Return composite stream from client
    def get_composite(self):
        return self.connection.get_composite(
                self.compose,
                **self.query_params())

    # Load composite stream and hydrate attributes
    def load(self):
        data = self.get_composite()
        self.measurements = data['measurements']
        self.query = data.get('query', {})
        self.resolution = data.get('resolution')
        return data

    def sources(self, unique=True):
        result = [m['source']['name'] for m in self.measurements if m['source']]
        if unique:
            return sorted(set(result))
        else:
            return result

    def series(self, metric=None):
        if metric:
            return [m['series'] for m in self.measurements if m['metric']['name'] == metric]
        else:
            return [m['series'] for m in self.measurements]

    def metrics(self, unique=True):
        result = [m['metric']['name'] for m in self.measurements if m['metric']]
        if unique:
            return sorted(set(result))
        else:
            return result

    def measure_times(self, metric=None):
        return self.map_field_from_series('measure_time', metric)

    def values(self, metric=None):
        return self.map_field_from_series('value', metric)

    def map_field_from_series(self, field, metric=None):
        return map(lambda row: map(lambda s: s[field], row), self.series(metric))

    def next_time(self):
        self.query['next_time']
