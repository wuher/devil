#  -*- coding: utf-8 -*-
# http.py ---
#
# Created: Wed Dec 14 15:09:35 2011 (+0200)
# Author: Janne Kuuskeri
#


CODES = dict(
    ALL_OK = ('OK', 200),
    CREATED = ('Created', 201),
    DELETED = ('No Content', 204),
    BAD_REQUEST = ('Bad Request', 400),
    UNAUTHORIZED = ('Unauthorized', 401),
    FORBIDDEN = ('Forbidden', 403),
    NOT_FOUND = ('Not Found', 404),
    METHOD_NOT_ALLOWED = ('Method Not Allowed', 405),
    NOT_ACCEPTABLE = ('Not Acceptable', 406),
    DUPLICATE_ENTRY = ('Conflict/Duplicate', 409),
    NOT_HERE = ('Gone', 410),
    INTERNAL_SERVER_ERROR = ('Internal Server Error', 500),
    NOT_IMPLEMENTED = ('Not Implemented', 501),
    THROTTLED = ('Throttled', 503),
    )
class Codes(object): pass
codes = Codes()
codes.__dict__.update(CODES)


class Response(object):
    def __init__(self, code, data, headers={}):
        self.code = code
        self.content = data
        self.headers = headers


#
# http.py ends here
