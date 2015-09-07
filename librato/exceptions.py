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
    #
    #
    # {
    #   "errors": {
    #     "request": "The requested data resolution is unavailable for the
    #                   given time range. Please try a different resolution."
    #   }
    # }
    #
    def _parse_error_message(self):
        if isinstance(self.error_payload, str):
            # Payload is just a string
            return self.error_payload
        elif isinstance(self.error_payload, dict):
            payload = self.error_payload['errors']
            messages = []
            for key in payload:
                error_list = payload[key]
                if isinstance(error_list, str):
                    # The error message is a scalar string, just tack it on
                    msg = "%s: %s" % (key, error_list)
                    messages.append(msg)
                elif isinstance(error_list, list):
                    for error_message in error_list:
                        msg = "%s: %s" % (key, error_message)
                        messages.append(msg)
                elif isinstance(error_list, dict):
                    for k in error_list:
                        # e.g. "params: measure_time: "
                        msg = "%s: %s: " % (key, k)
                        msg += self._flatten_error_message(error_list[k])
                        messages.append(msg)
            return ", ".join(messages)

    def _flatten_error_message(self, error_msg):
        if isinstance(error_msg, str):
            return error_msg
        elif isinstance(error_msg, list):
            # Join with commas
            return ", ".join(error_msg)
        elif isinstance(error_msg, dict):
            # Flatten out the dict
            for k in error_msg:
                messages = ", ".join(error_msg[k])
                return "%s: %s" % (k, messages)


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
