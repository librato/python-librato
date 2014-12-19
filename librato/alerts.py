

class Alert(object):
    """Librato Alert Base class"""

    def __init__(self, connection, name, id=None, description=None, version=2, conditions=[], services=[], attributes=[], active=True,rearm_seconds=None):
        self.connection = connection
        self.name = name
        self.description = description
        self.version = version
        self.conditions = []
        self.services = []
        self.attributes = attributes
        self.active = active
        self.rearm_seconds = rearm_seconds
        self.id = id

    @classmethod
    def from_dict(cls, connection, data):
        """Returns an alert object from a dictionary item,
        which is usually from librato's API"""
        obj = cls(connection,
                  data['name'],
                  conditions=data['conditions'],
                  services=data['services'],
                  id=data['id'],
                  attributes=data['attributes'])
        return obj
