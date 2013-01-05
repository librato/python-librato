# Copyright (c) 2012 Chris Moyer http://coredumped.org
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


class ClientError(Exception):
	"""4xx client exceptions"""
	def __init__(self, code, msg=None):
		self.code = code
		msg = "[%s] %s" % (code, msg)
		Exception.__init__(self, msg)

class BadRequest(ClientError):
	"""400 Forbidden"""
	def __init__(self, msg=None):
		ClientError.__init__(self,400, msg)

class Unauthorized(ClientError):
	"""401 Unauthorized"""
	def __init__(self, msg=None):
		ClientError.__init__(self,401, msg)

class Forbidden(ClientError):
	"""403 Forbidden"""
	def __init__(self, msg=None):
		ClientError.__init__(self,403, msg)

class NotFound(ClientError):
	"""404 Forbidden"""
	def __init__(self, msg=None):
		ClientError.__init__(self,404, msg)

CODES = {
	400: BadRequest,
	401: Unauthorized,
	403: Forbidden,
	404: NotFound
}


def get(code, resp_data):
	msg = ""
	if resp_data:
		msg = ""
		for key in resp_data['errors']:
			for v in resp_data['errors'][key]:
				for m in resp_data['errors'][key][v]:
					msg += "%s: %s %s\n" % (key, v, m)
	if CODES.has_key(code):
		return CODES[code](msg)
	else:
		return ClientError(code, msg)
