
class Instrument(object):
    """Librato Instrument Base class"""

    def __init__(self, connection, name, id=None, streams=[], attributes={}, description=None):
        self.connection = connection
        self.name = name
        self.streams = []
        for i in streams:
            if isinstance(i, Stream):
                self.streams.append(i)
            elif isinstance(i, dict):  # Probably parsing JSON here
                self.streams.append(Stream.from_dict(i))
            else:
                self.streams.append(Stream(*i))
        self.attributes = attributes
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """Returns a metric object from a dictionary item,
        which is usually from librato's API"""
        obj = cls(connection,
                  data['name'],
                  streams=data['streams'],
                  id=data['id'],
                  attributes=data['attributes'])
        return obj

    def get_payload(self):
        return {'name': self.name,
                'attributes': self.attributes,
                'streams': self.streams_payload()}

    def new_stream(self, *args, **kwargs):
        stream = Stream(*args, **kwargs)
        self.streams.append(stream)
        return stream

    def streams_payload(self):
        return [s.get_payload() for s in self.streams]

    def is_persisted(self):
        return self.id is not None

    def save(self):
        if not self.is_persisted():
            dummy_inst = self.connection.create_instrument(
                    self.name,
                    attributes=self.attributes,
                    streams=self.streams_payload())
            self.id = dummy_inst.id
        else:
            self.connection.update_instrument(self)


class Stream(object):
    def __init__(self, metric=None, source='*', composite=None, name=None,
            units_short=None, units_long=None, display_min=None, display_max=None,
            summary_function='average', transform_function=None, period=None,
            group_function='average', color=None):
        self.metric = metric
        self.composite = composite
        self.source = source
        self.name = name
        self.units_short = units_short
        self.units_long = units_long
        self.display_min = display_min
        self.display_max = display_max
        self.summary_function = summary_function
        self.transform_function = transform_function
        self.period = period
        self.group_function = group_function
        self.color = color

        if self.composite:
            self.source = None
            self.group_function = None

    @classmethod
    def from_dict(cls, data):
        """Returns a instrument object from a dictionary item,
        which is usually from librato's API"""

        obj = cls(data.get('metric'), data.get('source'), data.get('composite'),
            data.get('name'), data.get('units_short'), data.get('units_long'),
            data.get('min'), data.get('max'), data.get('summary_function'),
            data.get('transform_function'), data.get('period'),
            data.get('group_function'), data.get('color'))
        return obj

    def get_payload(self):
        return {'metric': self.metric,
                'composite': self.composite,
                'source': self.source,
                'name': self.name,
                'units_short': self.units_short,
                'units_long': self.units_long,
                'min': self.display_min,
                'max': self.display_max,
                'summary_function': self.summary_function,
                'transform_function': self.transform_function,
                'period': self.period,
                'group_function': self.group_function,
                'color': self.color}
