#  -*- coding: utf-8 -*-
# errors.py ---
#
# Created: Wed Dec 14 14:00:51 2011 (+0200)
# Author: Janne Kuuskeri
#


from http import codes


class HttpStatusCodeError(Exception):
    def __init__(self, code, content=None, *args, **kw):
        self.code = code
        self.content = content
        Exception.__init__(self, *args, **kw)

    def get_code(self):
        try:
            return self.code[1]
        except TypeError:
            # maybe int code was given instead..
            return self.code


class BadRequest(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.BAD_REQUEST)


class NotFound(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.NOT_FOUND)


class MethodNotAllowed(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.NOT_FOUND)


#
# errors.py ends here
