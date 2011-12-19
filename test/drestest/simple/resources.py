#  -*- coding: utf-8 -*-
# resources.py ---
#
# Created: Wed Dec 14 23:04:38 2011 (+0200)
# Author: Janne Kuuskeri
#


from drest.resource import Resource
from drest.http import Response


class MyRespResource(Resource):
    def get(self, request, *args, **kw):
        return Response(200, {'jedi': 'luke'})

class MyDictResource(Resource):
    """
    curl http://localhost:8000/simple/mapper/dict/?format=json -d '{"a": 1}' -X PUT --header "Content-Type: application/json"
    """

    def put(self, data, request, *args, **kw):
        self.mydata = data

    def get(self, request, *args, **kw):
        return {'a': 3, 'b': 4}

class MyTextResource(Resource):
    def get(self, request, *args, **kw):
        return 'hello text'


#
# resources.py ends here
