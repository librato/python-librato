#!/usr/bin/env python
import librato
import random
import json
import os

from librato.aggregator import Aggregator

print librato.__version__

cities =  {
    'europe': ["paris", "barcelona", "madrid"],
    'usa'   : [
        {"name": "sf", "station": 1},
        {"name": "new york", "station": 2},
        {"name": "austin", "station": 3},
    ]
}

def rand():
    return random.randint(20, 40)

def test_aggregation(metric_name, api):
    for city in cities['europe']:
        a = Aggregator(api, source="%s" % city, period=10)
        for i in range(10):
            a.add(metric_name, rand())
        a.submit()

    for city in cities['usa']:
        name, station = city['name'], city['station']
        a = Aggregator(api, period=10, tags={'city': name, 'station': station})
        for i in range(10):
            a.add_tagged(metric_name + "_MD", rand())
        a.submit()


def test_queue(metric_name, api):
    q = api.new_queue()

    a = q.add;
    at = q.add_tagged;

    a(metric_name, rand(), source="paris")
    a(metric_name, rand(), source="barcelona")
    a(metric_name, rand(), source="madrid")

    at(metric_name + "_MD", rand(), tags={'city': 'sf', 'station': '1'})
    at(metric_name + "_MD", rand(), tags={'city': 'new york', 'station': '1'})
    at(metric_name + "_MD", rand(), tags={'city': 'austin', 'station': '1'})

    q.submit()

def send(metric_name, api):
    st = api.submit_tagged
    s  = api.submit

    s(metric_name, rand(), source="paris", description= "temp SD")
    s(metric_name, rand(), source="barcelona", description= "temp SD")
    s(metric_name, rand(), source="madrid", description= "temp SD")

    s(metric_name + "_MD", rand(), tags={'city': 'sf', 'station': '1'})
    s(metric_name + "_MD", rand(), tags={'city': 'new york', 'station': '12'})
    s(metric_name + "_MD", rand(), tags={'city': 'austin', 'station': '27'})

def dump(h):
    print json.dumps(h, indent=4, separators=(',', ': '))

def get(metric_name, api):
    print "--- SD ---"
    m = api.get(metric_name, count=10, duration=300, resolution=1)
    for s in m.measurements.keys():
        print s, len(m.measurements[s])

    print "--- MD ---"
    resp = api.get_tagged(metric_name + "_MD", duration=300)
    for s in resp['series']:
        print s['tags'], len(s['measurements'])


metric_name = 'drd_temperature'
api = librato.connect(os.environ['LIBRATO_USER_PRD'], os.environ['LIBRATO_TOKEN_PRD'])

#test = 'basic'
#test = 'queue'
test = 'aggregation'
if test == 'basic':
    send(metric_name, api)
    get(metric_name, api)
if test == 'queue':
    test_queue(metric_name, api)
    get(metric_name, api)
if test == 'aggregation':
    test_aggregation(metric_name, api)
    get(metric_name, api)
