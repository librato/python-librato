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


class Queue(object):
    """Sending small amounts of measurements in a single HTTP request
    is inefficient. The payload is small and the overhead in the server
    for storing a single measurement is not worth it.

    This class allows the user to queue measurements which will be sent in a
    efficient manner. It allows both legacy and tagged measurements to be
    sent to Librato.

    Chunks are dicts of JSON objects for POST /metrics request.
    Legacy measurements have two keys 'gauges' and 'counters'. The value of these keys
    are lists of dict measurements.
    Tagged measurements have a 'measurements' key, whose value is a list of dict measurements.

    When the user sends a .submit() we iterate over the list of chunks and
    send one at a time.
    """
    MAX_MEASUREMENTS_PER_CHUNK = 300  # based docs; on POST /metrics

    def __init__(self, connection, auto_submit_count=None, tags={}):
        self.connection = connection
        self.tags = dict(tags)
        self.chunks = []
        self.tagged_chunks = []
        self.auto_submit_count = auto_submit_count

    # Get a shallow copy of the top-level tag set
    def get_tags(self):
        return dict(self.tags)

    # Define the top-level tag set for posting measurements
    def set_tags(self, d):
        self.tags = dict(d)    # Create a copy

    # Add one or more top-level tags for posting measurements
    def add_tags(self, d):
        self.tags.update(d)

    def add(self, name, value, type='gauge', **query_props):
        if 'tags' in query_props:
            self.add_tagged(name, value, **query_props)
        else:
            nm = {}  # new measurement
            nm['name'] = self.connection.sanitize(name)
            nm['value'] = value

            for pn, v in query_props.items():
                nm[pn] = v

            self._add_measurement(type, nm)
            self._auto_submit_if_necessary()

    def add_tagged(self, name, value, **query_props):
        nm = {}  # new measurement
        nm['name'] = self.connection.sanitize(name)
        nm['sum'] = value
        nm['count'] = 1

        for pn, v in query_props.items():
            nm[pn] = v

        self._add_tagged_measurement(nm)
        self._auto_submit_if_necessary()

    def add_aggregator(self, aggregator):
        cloned_measurements = dict(aggregator.measurements)

        # Find measure_time, if any
        mt = aggregator.get_measure_time()

        for name in cloned_measurements:
            nm = cloned_measurements[name]
            # Set metric name
            nm['name'] = name
            # Set measure_time
            if mt:
                nm['measure_time'] = mt
            # Set source
            if aggregator.source:
                nm['source'] = aggregator.source
            self._add_measurement('gauge', nm)

        tagged_measurements = dict(aggregator.tagged_measurements)
        for name in tagged_measurements:
            nm = tagged_measurements[name]

            nm['name'] = name
            if mt:
                nm['time'] = mt

            if aggregator.tags:
                if 'tags' not in nm:
                    nm['tags'] = {}
                nm['tags'].update(aggregator.tags)

            self._add_tagged_measurement(nm)

        # Clear measurements from aggregator
        aggregator.clear()

        self._auto_submit_if_necessary()

    def submit(self):
        for c in self.chunks:
            self.connection._mexe("metrics", method="POST", query_props=c)
        self.chunks = []

        for c in self.tagged_chunks:
            if 'tags' in c:
                c['tags'] = dict(self.tags).update(c['tags'])
            elif self.tags:
                c['tags'] = dict(self.tags)
            self.connection._mexe("measurements", method="POST", query_props=c)
        self.tagged_chunks = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.submit()

    # Private, sort of.
    #
    def _auto_submit_if_necessary(self):
        if self.auto_submit_count and self._num_measurements_in_queue() >= self.auto_submit_count:
            self.submit()

    def _add_measurement(self, type, nm):
        if not self.chunks or self._num_measurements_in_current_chunk() == self.MAX_MEASUREMENTS_PER_CHUNK:
            self.chunks.append({'gauges': [], 'counters': []})
        self.chunks[-1][type + 's'].append(nm)

    def _add_tagged_measurement(self, nm):
        if (not self.tagged_chunks or
           self._num_measurements_in_current_chunk(tagged=True) == self.MAX_MEASUREMENTS_PER_CHUNK):
            self.tagged_chunks.append({'measurements': []})
        self.tagged_chunks[-1]['measurements'].append(nm)

    def _current_chunk(self, tagged=False):
        if tagged:
            return self.tagged_chunks[-1] if self.tagged_chunks else None
        else:
            return self.chunks[-1] if self.chunks else None

    def _num_measurements_in_current_chunk(self, tagged=False):
        if tagged:
            if self.tagged_chunks:
                return len(self.tagged_chunks[-1]['measurements'])
            else:
                return 0
        else:
            if self.chunks:
                cc = self.chunks[-1]
                return len(cc['gauges']) + len(cc['counters'])
            else:
                return 0

    def _num_measurements_in_queue(self):
        num = 0
        if self.chunks:
            num += self._num_measurements_in_current_chunk() + self.MAX_MEASUREMENTS_PER_CHUNK * (len(self.chunks) - 1)
        if self.tagged_chunks:
            num += (self._num_measurements_in_current_chunk(tagged=True) +
                    self.MAX_MEASUREMENTS_PER_CHUNK * (len(self.tagged_chunks) - 1))
        return num
