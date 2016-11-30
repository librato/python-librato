#!/usr/bin/env python
import librato
import random
import logging
import json
import os
from optparse import OptionParser

from librato.aggregator import Aggregator


class Scratch(object):
    cities = {
        'europe': ["paris", "barcelona", "madrid"],
        'usa': [
            {"name": "sf", "station": 1},
            {"name": "new york", "station": 2},
            {"name": "austin", "station": 3},
        ]
    }

    def __init__(self, metric_name):
        self.metric_name = metric_name
        self.api = librato.connect(
                   os.environ['LIBRATO_USER_PRD'],
                   os.environ['LIBRATO_TOKEN_PRD']
                   )
        self.foo = 1

    def rand(self):
        return random.randint(20, 40)

    def name(self):
        return self.metric_name

    def md_name(self):
        return self.metric_name + "_MD"

    def test_spaces(self):
        self.create_sd_space()
        self.create_md_space()

    def create_md_space(self):
        space_name = "__py_test_spaces_MD"
        api = self.api

        space = api.find_space(space_name)
        if space:
            print "Deleting ", space_name
            api.delete_space(space.id)

        space = self.api.create_space(space_name, tags=True)

        linechart = api.create_chart(
            'cities MD line chart',
            space,
            streams=[
                {
                    "metric": self.md_name(),
                    "group_function": "breakout",
                    "summary_function": "average",
                    "tags": [
                        {"grouped": False, "name": "city", "values": ["%"]},
                        {"grouped": False, "name": "station", "values": ["%"]}
                    ],
                    "tags_filter": "custom",
                }
            ]
        )
        print "Adding linechart: ", linechart.id

        bn = api.create_chart(
            'temperature in austin',
            space,
            use_last_value=True,
            label="C",
            type="bignumber",
            streams=[
                {
                    "metric": self.md_name(),
                    "group_function": "average",
                    "summary_function": "average",
                    "tags": [
                        {"grouped": False, "name": "city", "values": ["austin*"]}
                    ],
                    "tags_filter": "custom",
                }
            ]
        )
        print "Adding BN: ", bn.id

        params = '?tag_set=%5B%7B%22name%22%3A%22city%22%2C%22grouped%22%3Afalse%2C%22values%22%3A%5B%22%2A%22%5D%7D%5D'
        print "https://metrics.librato.com/s/spaces/%s%s" % (space.id, params)

    def create_sd_space(self):
        space_name = "__py_test_spaces_SD"
        api = self.api

        space = api.find_space(space_name)
        if space:
            print "Deleting ", space_name
            api.delete_space(space.id)

        space = self.api.create_space(space_name)
        print "Created %s %s " % (space.name, str(space.id))

        linechart = api.create_chart(
            'cities SD',
            space,
            streams=[{'metric': self.name(), 'source': '*'}]
        )
        print "Adding linechart: ", linechart.id

        bn = space.add_chart(
            'temp in madrid',
            type='bignumber',
            label='C',
            use_last_value='true',
            streams=[{'metric': self.name(), 'source': 'madrid'}]
        )
        print "Adding BN chart: ", bn.id
        print "https://metrics.librato.com/s/spaces/%s" % space.id

    def test_aggregation(self):
        for city in self.cities['europe']:
            a = Aggregator(self.api, source="%s" % city, period=10)
            for i in range(10):
                a.add(self.name(), self.rand())
            a.submit()

        for city in self.cities['usa']:
            name, station = city['name'], city['station']
            a = Aggregator(
                self.api,
                period=10,
                tags={'city': name, 'station': station}
            )
            for i in range(10):
                a.add_tagged(self.md_name(), self.rand())
            a.submit()

    def test_queue(self):
        rand = self.rand
        q = self.api.new_queue()

        a = q.add
        # at = q.add_tagged

        a(self.name(), rand(), source="paris")
        a(self.name(), rand(), source="barcelona")
        a(self.name(), rand(), source="madrid")

        # Use regular submit with tags
        a(self.md_name(), rand(), tags={'city': 'sf', 'station': '1'})
        a(self.md_name(), rand(), tags={'city': 'new york', 'station': '1'})
        a(self.md_name(), rand(), tags={'city': 'austin', 'station': '1'})

        q.submit()

    def send(self):
        rand = self.rand
        # st = self.api.submit_tagged
        s = self.api.submit

        s(self.name(), rand(), source="paris", description="temp SD")
        s(self.name(), rand(), source="barcelona", description="temp SD")
        s(self.name(), rand(), source="madrid", description="temp SD")

        # Use transparent submit
        s(self.md_name(), rand(), tags={'city': 'sf', 'station': '1'})
        s(self.md_name(), rand(), tags={'city': 'new york', 'station': '12'})
        s(self.md_name(), rand(), tags={'city': 'austin', 'station': '27'})

    def dump(self, h):
        print json.dumps(h, indent=4, separators=(',', ': '))

    def get(self):
        print "--- SD ---: ", \
            "https://metrics.librato.com/s/spaces/340598?duration=1800"
        m = self.api.get(self.name(), count=10, duration=300, resolution=1)
        for s in m.measurements.keys():
            print s, len(m.measurements[s])

        print "--- MD ---: https://metrics.librato.com/s/spaces/340599?duration=300&tag_set=%5B%7B%22name%22%3A%22city%22%2C%22grouped%22%3Afalse%2C%22values%22%3A%5B%22%2A%22%5D%7D%5D"  # noqa
        resp = self.api.get_tagged(self.md_name(), duration=300)
        for s in resp['series']:
            print s['tags'], len(s['measurements'])

    def run(self, a):
        actions = {
            'send': self.send,
            'get': self.get,
            'queue': self.test_queue,
            'aggregation': self.test_aggregation,
            'spaces': self.test_spaces
        }
        if a in actions:
            actions[a]()
        else:
            print "Unknown action: <%s>. Bailing out." % a
            print "Valid actions: "
            for k in actions.keys():
                print "-", k


def main():
    parser = OptionParser()
    parser.add_option(
        "-a", "--action",
        dest="action",
        help="run action",
        default="basic"
    )
    parser.add_option(
        "-d", "--debug",
        action="store_true",
        help="enable http debugging",
        default=False
    )

    (options, args) = parser.parse_args()
    print librato.__version__
    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
    Scratch("drd_temperature").run(options.action)

main()
