# Defaults
HOSTNAME  = "metrics-api.librato.com"
BASE_PATH = "/v1/"

class Connection(object):
  def __init__(self, username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
    self.username  = username
    self.api_key   = api_key
    self.hostname  = hostname
    self.base_path = base_path

