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

import time

class Aggregator(object):
    """ Implements client-side *gauge* aggregation to reduce the number of measurements
    submitted.
    Specify a period (default: None) and the aggregator will automatically
    floor the measure_times to that interval.
    """

    def __init__(self, connection, **args):
        self.connection = connection
        # Global source for all metrics sent into the aggregator
        self.source = args.get('source')
        self.measurements = {}
        self.period = args.get('period')
        self.measure_time = args.get('measure_time')


    def add(self, name, value):
        if name not in self.measurements:
            self.measurements[name] = {
                'count': 1,
                'sum': value,
                'min': value,
                'max': value
                }
        else:
            m = self.measurements[name]
            m['sum'] += value
            m['count'] += 1
            if value < m['min']:
                m['min'] = value
            if value > m['max']:
                m['max'] = value

        return self.measurements


    def to_payload(self):
        # Map measurements into Librato POST (array) format
        # {
        #     'gauges': [
        #         {'count': 1, 'max': 42, 'sum': 42, 'name': 'foo', 'min': 42}
        #     ]
        #    'measure_time': 1418838418 (optional)
        #    'source': 'mysource' (optional)
        # }
        # Note: hash format would work too, but the mocks aren't currently set up
        # for the hash format :-(
        # i.e. result = {'gauges': dict(self.measurements)}

        body = []
        for metric_name in self.measurements:
            # Create a clone so we don't change self.measurements
            vals = dict(self.measurements[metric_name])
            vals["name"] = metric_name
            body.append(vals)

        result = {'gauges': body}

        if self.source:
            result['source'] = self.source

        mt = self.floor_measure_time()
        if mt:
            result['measure_time'] = mt

        return result


    # Get/set the measure time if it is ever queried, that way you'll know the measure_time
    # that was submitted, and we'll guarantee the same measure_time for all measurements
    # extracted into a queue
    def get_measure_time(self):
        mt = self.floor_measure_time()
        if mt:
            self.measure_time = mt
        return self.measure_time

    # Return floored measure time if period is set
    # otherwise return user specified value if set
    # otherwise return none
    def floor_measure_time(self):
        if self.period:
            mt = None
            if self.measure_time:
                # Use user-specified time
                mt = self.measure_time
            else:
                # Grab wall time
                mt = int(time.time())
            return mt - (mt % self.period)
        elif self.measure_time:
            # Use the user-specified value with no flooring
            return self.measure_time


    def clear(self):
        self.measurements = {}
        self.measure_time = None


    def submit(self):
        # Submit measurements to API
        # This will actually return an empty 200 response (no body)
        self.connection._mexe("metrics",
                method="POST",
                query_props=self.to_payload())
        # Clear measurements
        self.clear()

