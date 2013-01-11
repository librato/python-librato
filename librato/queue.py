
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
  MAX_MEASUREMENTS_PER_CHUNK = 5000

  def __init__(self, connection):
    self.connection = connection
    self.chunks = [ self._gen_empty_chunk() ]

  def add(self, metric_name, value, type='gauge', **query_props):
    nm = {} # new measurement
    nm['name']  = metric_name
    nm['value'] = value
    nm['type']  = type
    for pn, v in query_props.items():
      nm[pn] = v

    self._add_measurement(type, nm)

  def submit(self):
    for c in self.chunks:
      self.connection._mexe("metrics", method="POST", query_props=c)
    self.chunks = [ self._gen_empty_chunk() ]

  # Private, sort of.
  #
  def _gen_empty_chunk(self):
    return { 'gauges': [], 'counters': [] }

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

