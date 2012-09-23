#  -*- coding: utf-8 -*-
#  Representation.py ---
#


from django import forms
from copy import deepcopy
from django.core.exceptions import ValidationError


__all__ = ('Representation',)


class BaseRepresentation(object):
    """ Base class for actual Representation class.

    You shouldn't need to use this directly. Always subclass from
    :class:`Representation`.
    """

    def __init__(self):
        """ Create the ``fields`` property.

        ``base_fields`` is left as a backup. You shouldn't modify it.
        """

        self.fields = deepcopy(self.base_fields)

    def validate(self, data=None):
        """ Validate the data

        Check also that no extra properties are present.

        :raises: ValidationError if the data is not valid.
        """

        errors = {}

        # validate each field, one by one
        for name, field in self.fields.items():
            try:
                field.clean(data.get(name))
            except ValidationError, e:
                errors[name] = e.messages

        # check for extra fields
        extras = set(data.keys()) - set(self.fields.keys())
        if extras:
            errors[', '.join(extras)] = ['field(s) not allowed']

        # if errors, raise ValidationError
        if errors:
            raise ValidationError(errors)


def get_declared_fields(bases, attrs):
    """ Find all fields and return them as a dictionary.

    note:: this is function is copied and modified
        from django.forms.get_declared_fields
    """

    def is_field(prop):
        return isinstance(prop, forms.Field) or \
            isinstance(prop, BaseRepresentation)

    fields = [(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if is_field(obj)]
    # add fields from base classes:
    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = base.base_fields.items() + fields
    return dict(fields)


class RepresentationMeta(type):
    """ Metaclass for Representations.

    This will find all fields defined for a Representation and stick them
    in a dictionary in ``base_fields`` property.
    """

    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = get_declared_fields(bases, attrs)
        return super(RepresentationMeta, cls).__new__(cls, name, bases, attrs)


class Representation(BaseRepresentation):
    """ Base class for all Representations.

    Subclass this for your own Representation. Only two properties are
    required from Representations: ``validate`` method and ``fields`` property.

    Representations are used for two purposes: to validate data and to perform
    object creation/serialization by object factories.

    seealso:: :class:`BaseRepresentation` for details on methods.
    """

    __metaclass__ = RepresentationMeta


#
#  Representation.py ends here
