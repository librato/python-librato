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
    efficient matter.

    Chunks are dicts of JSON objects for POST /metrics request.
    They have two keys 'gauges' and 'counters'. The value of these keys
    are lists of dict measurements.

    When the user sends a .submit() we iterate over the list of chunks and
    send one at a time.
    """
    MAX_MEASUREMENTS_PER_CHUNK = 300  # based docs; on POST /metrics

    def __init__(self, connection):
        self.connection = connection
        self.chunks = [self._gen_empty_chunk()]

    def add(self, name, value, type='gauge', **query_props):
        nm = {}  # new measurement
        nm['name'] = name
        nm['value'] = value
        nm['type'] = type
        for pn, v in query_props.items():
            nm[pn] = v

        self._add_measurement(type, nm)

    def submit(self):
        for c in self.chunks:
            self.connection._mexe("metrics", method="POST", query_props=c)
        self.chunks = [self._gen_empty_chunk()]

    # Private, sort of.
    #
    def _gen_empty_chunk(self):
        return {'gauges': [], 'counters': []}

    def _create_new_chunk_if_needed(self):
        if self._reached_max_measurements_per_chunk():
            self.chunks.append(self._gen_empty_chunk())

    def _reached_max_measurements_per_chunk(self):
        return self._num_measurements_in_current_chunk() == \
            self.MAX_MEASUREMENTS_PER_CHUNK

    def _add_measurement(self, type, nm):
        self._create_new_chunk_if_needed()
        self._current_chunk()[type + 's'].append(nm)

    def _num_measurements_in_current_chunk(self):
        cc = self._current_chunk()
        return len(cc['gauges']) + len(cc['counters'])

    def _current_chunk(self):
        return self.chunks[-1]
