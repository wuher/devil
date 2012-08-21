#  -*- coding: utf-8 -*-
#  resources.py ---
#  created: 2012-07-29 23:01:32
#  Author: Janne Kuuskeri
#


from django.forms import fields
from devil import DocumentedResource
from devil.fields import Representation


class MyTestResource(DocumentedResource):
    """ My test resource

    description of my resource
    """

    class MyRepresentation(Representation):
        name = fields.CharField(max_length=30, required=False)
        age = fields.IntegerField(required=False)
        weight = fields.IntegerField()

    representation = MyRepresentation()

    def get(self, *args, **kw):
        """ hiihoo get

        hiihoo description
        """

        return 'hiihoo'


#
#  resources.py ends here
