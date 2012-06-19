#  -*- coding: utf-8 -*-
#  fields.py ---
#  created: 2012-05-20 14:32:31
#


from django.core.exceptions import ValidationError
from django import forms


__all__ = ('DevilField',)


#
# Field definitions.
#


class DevilField(forms.Field):
    """ Base class for all custom fields defined in Jinx.

    note:: All fields used in specifications need to inherit from this class.

    Django's fields can't be used directly in specifications as other code
    depends on these three functions to be there for each field.
    """

    empty_values = (None,)

    def __init__(self, alias=None, *args, **kw):
        """ Store init data.

        :param alias: an alias for this field that should be used
            when this field is converted between entitys and dict.
        """

        self.alias = alias
        super(DevilField, self).__init__(*args, **kw)

    def validate(self, value):
        """ This was overridden to have our own ``empty_values``. """
        if value in self.empty_values and self.required:
            raise ValidationError(self.error_messages['required'])


#
#  fields.py ends here
