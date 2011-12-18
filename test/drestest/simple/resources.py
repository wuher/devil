#  -*- coding: utf-8 -*-
# resources.py ---
#
# Created: Wed Dec 14 23:04:38 2011 (+0200)
# Author: Janne Kuuskeri
#


from drest.resource import Resource


class MyTestResource(Resource):
    def get(self, request, *args, **kw):
        return {'a': 3, 'b': 4}


#
# resources.py ends here
