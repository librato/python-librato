class Alert(object):
    """Librato Alert Base class"""

    def __init__(self, connection, name, _id=None, description=None, version=2, conditions=[], services=[], attributes={}, active=True, rearm_seconds=None):
        self.connection = connection
        self.name = name
        self.description = description
        self.version = version
        self.conditions = []
        for c in conditions:
            if isinstance(c, Condition):
                self.conditions.append(c)
            elif isinstance(c, dict):  # Probably parsing JSON here
                self.conditions.append(Condition.from_dict(c))
            else:
                self.conditions.append(Condition(*c))
        self.services = []
        for s in services:
            if isinstance(s, Service):
                self.services.append(s)
            elif isinstance(s, dict):  # Probably parsing JSON here
                self.services.append(Service.from_dict(s))
            elif isinstance(s, int):
                self.services.append(Service(s))
            else:
                self.services.append(Service(*s))
        self.attributes = attributes
        self.active = active
        self.rearm_seconds = rearm_seconds
        self._id = _id

    def add_condition_for(self, metric_name, source='*'):
        condition = Condition(metric_name, source)
        self.conditions.append(condition)
        return condition

    def add_service(self, service_id):
        self.services.append(Service(service_id))

    @classmethod
    def from_dict(cls, connection, data):
        """Returns an alert object from a dictionary item,
        which is usually from librato's API"""
        obj = cls(connection,
                  data['name'],
                  version=data['version'],
                  description=data['description'],
                  conditions=data['conditions'],
                  services=data['services'],
                  _id=data['id'],
                  active=data['active'],
                  rearm_seconds=data['rearm_seconds'],
                  attributes=data['attributes'])
        return obj

    def get_payload(self):
        return {'name': self.name,
                'attributes': self.attributes,
                'version': self.version,
                'description': self.description,
                'rearm_seconds': self.rearm_seconds,
                'active': self.active,
                'services': [x._id for x in self.services],
                'conditions': [x.get_payload() for x in self.conditions]}

    def save(self):
        self.connection.update_alert(self)

class Condition(object):
    ABOVE = 'above'
    BELOW = 'below'
    ABSENT = 'absent'

    # Note this is 'average' not 'mean'
    SUMMARY_FUNCTION_AVERAGE = 'average'

    def __init__(self, metric_name, source='*'):
        self.metric_name = metric_name
        self.source = source
        self.summary_function = None

    def above(self, threshold, summary_function=SUMMARY_FUNCTION_AVERAGE):
        self.condition_type = self.ABOVE
        self.summary_function = summary_function
        self.threshold = threshold
        # This implies an immediate trigger
        self._duration = None
        return self

    def below(self, threshold, summary_function=SUMMARY_FUNCTION_AVERAGE):
        self.condition_type = self.BELOW
        self.summary_function = summary_function
        self.threshold = threshold
        # This implies an immediate trigger
        self._duration = None
        return self

    # Stops reporting for a duration (in seconds)
    def stops_reporting_for(self, duration):
        self.condition_type = self.ABSENT
        self.summary_function = None
        self._duration = duration
        return self

    def duration(self, duration):
        self._duration = duration

    # An alert condition is either "immediate" or "time windowed"
    def immediate(self):
        if self._duration is None or self._duration == 0:
            return True
        else:
            return False

    @classmethod
    def from_dict(cls, data):
        obj = cls(metric_name=data['metric_name'],
                  source=data['source'])
        if data['type'] == Condition.ABOVE:
            obj.above(data.get('threshold'), data.get('summary_function'))
            obj.duration(data.get('duration'))
        elif data['type'] == Condition.BELOW:
            obj.below(data.get('threshold'), data.get('summary_function'))
            obj.duration(data.get('duration'))
        elif data['type'] == Condition.ABSENT:
            obj.stops_reporting_for(data.get('duration'))
        return obj

    def get_payload(self):
        obj = {'condition_type': self.condition_type,
                'metric_name': self.metric_name,
                'source': self.source}
        if self.condition_type in [self.ABOVE, self.BELOW]:
            obj['threshold'] = self.threshold
            obj['summary_function'] = self.summary_function
            obj['duration'] = self._duration
        elif self.condition_type == self.ABSENT:
            obj['summary_function'] = self.summary_function
            obj['duration'] = self._duration
        return obj

class Service(object):
    def __init__(self, _id):
        self._id = _id
    @classmethod
    def from_dict(cls, data):
        obj = cls(_id=data['id'])
        return obj


    def get_payload(self):
        return {'id': self._id}
