

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
                self.conditions.append(Condition.from_dict(self, c))
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
                  conditions=data['conditions'],
                  services=data['services'],
                  _id=data['id'],
                  attributes=data['attributes'])
        return obj

    def get_payload(self):
        return {'name': self.name,
                'attributes': self.attributes,
                'version': self.version,
                'services': [x._id for x in self.services],
                'conditions': [x.get_payload() for x in self.conditions]}
    
    def save(self):
        self.connection.update_alert(self)

class Condition(object):
    def __init__(self, metric_name, source='*'):
        self.metric_name = metric_name
        self.source = source

    def above(self, threshold, summary_function=None):
        self.condition_type = 'above'
        self.summary_function = summary_function
        self.threshold = threshold
        self.duration = None
        return self

    def during(self, duration):
        self.duration = duration
    
    @classmethod
    def from_dict(cls, connection, data):
        obj = cls(metric_name=data['metric_name'],
                  source=data['source'])
        if data['type'] == 'above':
           obj.above(data.get('threshold'), data.get('summary_function')).during(data.get('duration'))
        return obj
    
    def get_payload(self):
        obj = {'condition_type': self.condition_type,
                'metric_name': self.metric_name,
                'source': self.source}
        if self.condition_type == 'above':
            obj['threshold'] = self.threshold
            obj['summary_function'] = self.summary_function
            obj['duration'] = self.duration
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
