#  -*- coding: utf-8 -*-
#  __init__.py ---
#  created: 2012-05-20 10:25:16
#


from django.forms import Field
from representation import *
from fields import *
from factory import *


#
# We amend django's Field class with two methods: serialize() and from_python().
# This way it's safe to invoke those functions in devil for all fields, may
# they be defined in django or by the application (derived from devil.Field).
# This is just a convenience and performance optimization.
#
# Django already provides the opposite of these two function in its Field
# implementation: clean() and to_python().
#

def serialize(self, value, entity=None, request=None):
    """ Validate and serialize the value.

    This is the default implementation
    """

    ret = self.from_python(value)
    self.validate(ret)
    self.run_validators(value)
    return ret


def from_python(self, value):
    return value


Field.alias = None
Field.serialize = serialize
Field.from_python = from_python


#
#  __init__.py ends here
