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
        if value in self.empty_values and self.required:
            # import pdb; pdb.set_trace()
            raise ValidationError(self.error_messages['required'])

    def clean(self, value):
        """ """
        return super(DevilField, self).clean(value)

    def serialize(self, value, entity, request):
        """ todo: remove the request parameter """
        # self.validate(value)
        # self.run_validators(value)
        return self.from_python(value)

    def from_python(self, value):
        """ opposite of ``to_python()`` """
        return value


#
#  fields.py ends here
