import requests
import json
from metrics import Metric


# Defaults
HOSTNAME  = "https://metrics-api.librato.com"
BASE_PATH = "/v1/"

class Connection(object):
  HOSTNAME  = "https://metrics-api.librato.com"
  BASE_PATH = "/v1/"

  def __init__(self, username, api_key, hostname=HOSTNAME, base_path=BASE_PATH):
    self.hostname  = hostname
    self.base_path = base_path
    self.auth      = (username, api_key)

  def _exe(self, end_path, method="GET", query_params=None, payload=None):
    url = self.hostname + self.base_path + end_path
    if method == "GET":
      response = requests.get(url, auth=self.auth, params=query_params)
      return json.loads(response.text)
    if method == "POST":
      requests.post(url, auth=self.auth, data=payload)

  def _parse(self, resp, name, cls):
    if resp.has_key(name):
      return [cls.from_dict(self, m) for m in resp[name]]
    else:
      return resp

  def list_metrics(self, **query_params):
    r = self._exe(end_path="metrics", query_params=query_params)
    return self._parse(resp=r, name="metrics", cls=Metric)
