#  -*- coding: utf-8 -*-
# errors.py ---
#
# Created: Wed Dec 14 14:00:51 2011 (+0200)
# Author: Janne Kuuskeri
#


from http import codes


class HttpStatusCodeError(Exception):
    """ Base class for all exceptions raising an HTTP error code. """

    def __init__(self, code, content=None, *args, **kw):
        """ Store code and content """
        self.code = code
        self.content = content
        Exception.__init__(self, *args, **kw)

    def get_code_num(self):
        try:
            return self.code[1]
        except TypeError:
            # maybe int code was given instead..
            return self.code

    def has_code(self, code):
        mycode = self.get_code_num()
        try:
            return mycode is code[1]
        except TypeError:
            return mycode is code


class BadRequest(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.BAD_REQUEST, *args, **kw)


class Unauthorized(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.UNAUTHORIZED, *args, **kw)

class Forbidden(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.FORBIDDEN, *args, **kw)

class NotFound(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.NOT_FOUND, *args, **kw)


class NotAcceptable(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.NOT_ACCEPTABLE, *args, **kw)


class MethodNotAllowed(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.METHOD_NOT_ALLOWED, *args, **kw)

class InternalServerError(HttpStatusCodeError):
    def __init__(self, *args, **kw):
        HttpStatusCodeError.__init__(self, codes.INTERNAL_SERVER_ERROR, *args, **kw)


#
# errors.py ends here
