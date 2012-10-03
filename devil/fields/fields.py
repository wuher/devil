#  -*- coding: utf-8 -*-
#  fields.py ---
#  created: 2012-05-20 14:32:31
#


from django.core.exceptions import ValidationError
from django import forms
from .representation import Representation
from .factory import Factory


__all__ = (
    'DevilField',
    'NestedField',
    'ListField',
    'EnumField',
    )


#
# Field definitions.
#


class DevilField(forms.Field):
    """ Base class for all fields defined by the application.

    Fields are assumed to have five functions:
      - ``validate()``: validate existance
      - ``to_python()``: convert given value from e.g. string to python object
      - ``clean()``: convert (using ``to_python()``) and validate the value
      - ``from_python()``: opposite of ``to_python()``
      - ``serialize()``: convert (using ``from_python()``) and validate

    You rarely need to invoke ``to_python()`` or ``from_python()`` yourself, but
    you may want to override them in derived field-classes to define how a field
    should be converted. Converserly, you rarely need to override ``clean()`` or
    ``serialize()`` but you do need to invoke them when you want to perform
    validation or cleaning/serialization.

    To perform validation on a given field::

        # field is of type IntegerField
        field.clean("34")

    To convert and validate a value from string to python object::

        # field is of type IntegerField
        field.clean("34")  # returns 34

    To convert and validate a value from python object to string::

        # field is of type DateField and d is python ``date`` object
        field.serialize(d)  # returns "2012-04-19"

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


class NestedField(Representation):
    """ Base class for complex fields.

    In Jinx, this would usually be used for value objects.

    This field is a field and specification at the same time.
    """

    empty_values = (None,)
    default_validators = []

    def __init__(
        self,
        required=True,
        validators=[],
        alias=None,
        *args, **kw):
        """ Parameters are the same as for other fields. """
        self.required = required
        self.validators = self.default_validators + validators
        self.alias = alias
        super(NestedField, self).__init__(*args, **kw)
        self.factory = Factory(klass=self.__class__, spec=self)

    def clean(self, value):
        """ Clean the data and validate the nested spec.

        Implementation is the same as for other fields but in addition,
        this will propagate the validation to the nested spec.
        """

        obj = self.factory.create(value)

        # todo: what if the field defines properties that have any of
        # these names:
        if obj:
            del obj.fields
            del obj.alias
            del obj.validators
            del obj.required
            del obj.factory

        # do own cleaning first...
        self._validate_existence(obj)
        self._run_validators(obj)

        # ret = {}
        # for name in self.fields.keys():
        #     ret[name] = getattr(obj, name)
        # return ret
        return obj

    def serialize(self, value, entity, request):
        """ Propagate to nested fields.

        :returns: data dictionary or ``None`` if no fields are present.
        """

        self._validate_existence(value)
        self._run_validators(value)

        if not value:
            return value

        return self.factory.serialize(value)

    def to_python(self, value):
        raise NotImplemented("nested field doesn't support to_python")

    def from_python(self, value):
        raise NotImplemented("nested field doesn't support from_python")

    def _validate_existence(self, value):
        """ Raise ``ValidationError`` if value should be present but isn't """
        if value in self.empty_values and self.required:
            raise ValidationError('this field is required')

    def _run_validators(self, value):
        """ Execute all associated validators. """
        errors = []
        for v in self.validators:
            try:
                v(value)
            except ValidationError, e:
                errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)


class ListValidator(object):
    def __call__(self, value):
        if not isinstance(value, (list, tuple)):
            raise ValidationError('illegal list value')


class ListField(DevilField):
    """ List field to support lists of fields. """

    empty_values = (None, [],)

    default_validators = [
        ListValidator()
    ]

    def __init__(self, itemspec, *args, **kw):
        """ Define the type of list items.

        :param itemspec: every item in the list must satisfy this field.
        :type itemspec: ``DevilField`` or its derivative.
        """

        self.itemspec = itemspec
        super(ListField, self).__init__(*args, **kw)

    def clean(self, value):
        """ Propagate to list elements. """
        value = super(ListField, self).clean(value)
        if value is not None:
            return map(self.itemspec.clean, value)

    def serialize(self, value, entity, request):
        """ Propagate to list elements. """
        value = super(ListField, self).serialize(value, entity, request)
        if value is None:
            return
        ret = []
        for v in value:
            ret.append(self.itemspec.serialize(v, entity, request))
        return ret


class EnumValidator(object):
    """ Validate that the value is one of the legal values. """

    def __init__(self, legal_values):
        self.legal_values = set(legal_values)

    def __call__(self, value):
        if value not in self.legal_values:
            raise ValidationError('illegal value for enum: %s' % (str(value),))


class EnumField(DevilField):
    """ Enumeration field.

    Usage example:

      weekday = EnumField(('mon', 'thu', 'wed', 'thu', 'fri'))
    """

    values = ()

    def __init__(self, values=None, *args, **kw):
        super(EnumField, self).__init__(*args, **kw)
        values = tuple(self.values) + tuple((values or ()))
        self.validators += [EnumValidator(set(values))]


#
#  fields.py ends here
