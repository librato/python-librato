# Copyright (c) 2013. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class ClientError(Exception):
    """4xx client exceptions"""
    def __init__(self, code, error_payload=None):
        self.code = code
        self.error_payload = error_payload
        Exception.__init__(self, self.error_message())

    def error_message(self):
        return "[%s] %s" % (self.code, self._parse_error_message())

    # See http://dev.librato.com/v1/responses-errors
    # Examples:
    # {
    #   "errors": {
    #     "params": {
    #       "name":["is not present"],
    #       "start_time":["is not a number"]
    #      }
    #    }
    #  }
    #
    #
    # {
    #   "errors": {
    #     "request": [
    #       "Please use secured connection through https!",
    #       "Please provide credentials for authentication."
    #     ]
    #   }
    # }
    def _parse_error_message(self):
        if isinstance(self.error_payload, str):
            # Normal string
            return self.error_payload
        elif isinstance(self.error_payload, dict):
            # Error hash
            errors = self.error_payload['errors']
            messages = []
            for key in errors:
                for v in errors[key]:
                    msg = "%s: %s" % (key, v)
                    if isinstance(errors[key], dict):
                        msg += ": "
                        if isinstance(errors[key][v], list):
                          # Join error messages with commas
                          msg += ", ".join(errors[key][v])
                        elif isinstance(errors[key][v], dict):
                          #TODO: refactor it
                          for vv in errors[key][v]:
                            msg += "%s: " % (vv)
                            msg += ", ".join(errors[key][v][vv])
                        else:
                          msg += errors[key][v]
                    messages.append(msg)
            return ", ".join(messages)


class BadRequest(ClientError):
    """400 Forbidden"""
    def __init__(self, msg=None):
        ClientError.__init__(self, 400, msg)


class Unauthorized(ClientError):
    """401 Unauthorized"""
    def __init__(self, msg=None):
        ClientError.__init__(self, 401, msg)


class Forbidden(ClientError):
    """403 Forbidden"""
    def __init__(self, msg=None):
        ClientError.__init__(self, 403, msg)


class NotFound(ClientError):
    """404 Forbidden"""
    def __init__(self, msg=None):
        ClientError.__init__(self, 404, msg)

CODES = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound
}

# http://dev.librato.com/v1/responses-errors
def get(code, resp_data):
    if code in CODES:
        return CODES[code](resp_data)
    else:
        return ClientError(code, resp_data)
