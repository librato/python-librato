class Stream(object):
    def __init__(self, metric=None, source='*', composite=None):
        self.metric = metric
        self.composite = composite
        self.source = source
        if self.composite:
            self.source = None

    def get_payload(self):
        return {'metric': self.metric,
                'composite': self.composite,
                'source': self.source}
