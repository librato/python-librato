

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
        self.attributes = attributes
        self.active = active
        self.rearm_seconds = rearm_seconds
        self._id = _id

    def add_condition(self, condition_type, threshold, metric):
        condition = Condition(condition_type, threshold, metric)
        self.conditions.append(condition)
        return condition

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
                'services': self.services,
                'conditions': [x.get_payload() for x in self.conditions]}
    
    def save(self):
        self.connection.update_alert(self)

class Condition(object):
    def __init__(self, condition_type, threshold, metric_name, source='*'):
        self.condition_type = condition_type
        self.threshold = threshold
        self.metric_name = metric_name
        self.source = source
    
    @classmethod
    def from_dict(cls, connection, data):
        """Returns a condition object from a dictionary item,
        which is usually from librato's API"""
        obj = cls(condition_type=data['type'],
                  threshold=data['threshold'],
                  metric_name=data['metric_name'],
                  source=data['source'])
        return obj


    def get_payload(self):
        return {'condition_type': self.condition_type,
                'threshold': self.threshold,
                'metric_name': self.metric_name,
                'source': self.source}
