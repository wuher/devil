#  -*- coding: utf-8 -*-
# auth.py ---
#
# Created: Wed Dec 21 09:36:05 2011 (+0200)
# Author: Janne Kuuskeri
#


import base64
from django.contrib.auth import authenticate
from errors import Unauthorized, Forbidden

class HttpBasic(object):
    def authenticate(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None:
                        if user.is_active:
                            request.user = user
                            return user
                    else:
                        raise Forbidden()

        # either no auth header or using some other auth protocol,
        # we'll return a challenge for the user anyway
        raise Unauthorized()


#
# auth.py ends here
