#  -*- coding: utf-8 -*-
#  factory.py ---
#


from copy import deepcopy
from django.core.exceptions import ValidationError


class Factory(object):
    """ Base class for all factories.

    Against common convention for implementing factories, this class also
    provides ``serialize()`` function which is the counter operation
    of ``create()``.

    Factory uses a *specification* to be able to do creation and serialization.
    A specification object must have a *fields* property that contains the types
    of all fields. Normally a *field* knows how to marshal/unmarshal itself but
    if not, a subclassed factory may provide ``create_foo`` and
    ``serialize_foo`` functions to provide custom creation/serialization.

    This factory supports name mangling of properties.

    For example:
        tripPurpose -> trip_purpose
        trip_purpose -> tripPurpose

    Fields may provide ``alias`` property so that we can find the serialized
    value when it's stored under different name than what's specified in the
    spec.
    """

    #: These values, when used as values of properties are considered as being
    #: missing or undefined. While serializing, they are omitted unless marked
    #: as being ``required``.
    missing = (None,)

    #: Do we raise ``ValidationError`` if input data contains extra fields?
    prevent_extra_fields = True

    #: Specification of the **incoming** data.
    spec = None

    #: todo
    default_create_values = {}

    def __init__(
        self,
        klass=None,
        spec=None,
        prevent_extra_fields=None):
        """ Offer possibility to override default values.

        :param klass: ``create()`` must return an instance of this class.
            If ``None``, ``create()`` will return ``dict``.
        :param spec: Specification of the incoming data. This must be a
            ``Representation`` like object.
        """

        if klass:
            self.klass = klass
        if spec:
            self.spec = spec
        if prevent_extra_fields is not None:
            self.prevent_extra_fields = prevent_extra_fields
        # generate key name mappings
        if self.spec:
            self.property_name_map = self._create_mappings(self.spec)

    def create(self, data):
        """ Create object from the given data.

        The given data may or may not have been validated prior to calling
        this function. This function will try its best in creating the object.
        If the resulting object cannot be produced, raises ``ValidationError``.

        The spec can affect how individual fields will be created by
        implementing ``clean()`` for the fields needing customization.

        :param data: the data as a dictionary.
        :return: instance of ``klass`` or dictionary.
        :raises: ``ValidationError`` if factory is unable to create object.
        """

        # todo: copy-paste code from representation.validate -> refactor

        if data is None:
            return None

        prototype = {}
        errors = {}

        # create and populate the prototype
        for field_name, field_spec in self.spec.fields.items():
            try:
                value = self._create_value(data, field_name, self.spec)
            except ValidationError, e:
                if field_name not in self.default_create_values:
                    errors[field_name] = e.messages
            else:
                key_name = self.property_name_map[field_name]
                prototype[key_name] = value

        # check extra fields
        if self.prevent_extra_fields:
            extras = set(data.keys()) - set(self.property_name_map.keys())
            if extras:
                errors[', '.join(extras)] = ['field(s) not allowed']

        # if errors, raise ValidationError
        if errors:
            raise ValidationError(errors)

        # return dict or object based on the prototype
        _data = deepcopy(self.default_create_values)
        _data.update(prototype)
        if self.klass:
            instance = self.klass()
            instance.__dict__.update(prototype)
            return instance
        else:
            return prototype

    def serialize(self, data, request=None):
        """ Serialize entity into dictionary.

        The spec can affect how individual fields will be serialized by
        implementing ``serialize()`` for the fields needing customization.

        :returns: dictionary
        """

        def should_we_insert(value, field_spec):
            return value not in self.missing or field_spec.required

        errors = {}
        ret = {}
        for field_name, field_spec in self.spec.fields.items():
            try:
                # get value as it is:
                value = self._get_value_for_serialization(data, field_name, field_spec)
                if should_we_insert(value, field_spec):
                    # value found -> serialize:
                    value = self._serialize_value(value, field_name, self.spec, data, request)
                    if should_we_insert(value, field_spec):
                        # we still have the value (even after serialization):
                        ret[field_name] = value
            except ValidationError, e:
                errors[field_name] = e.messages

        if errors:
            raise ValidationError(errors)

        return None if ret == {} else ret

    def _create_value(self, data, name, spec):
        """ Create the value for a field.

        :param data: the whole data for the entity (all fields).
        :param name: name of the initialized field.
        :param spec: spec for the whole entity.
        """

        field = getattr(self, 'create_' + name, None)
        if field:
            # this factory has a special creator function for this field
            return field(data, name, spec)
        value = data.get(name)
        return spec.fields[name].clean(value)

    def _serialize_value(self, value, name, spec, entity, request):
        """ Serialize a value suitable for data dictionary.

        :param value: the value of the entity's field.
        :param name: name of the field.
        :param spec: spec for the whole entity.
        :param entity: the whole entity (this may be interesting to
            more complex serializations).
        """

        serialize_func = self._get_serialize_func(name, spec)
        return serialize_func(value, entity, request)

    def _get_serialize_func(self, name, spec):
        """ Return the function that is used for serialization. """
        func = getattr(self, 'serialize_' + name, None)
        if func:
            # this factory has a special serializer function for this field
            return func
        func = getattr(spec.fields[name], 'serialize', None)
        if func:
            return func
        return lambda value, entity, request: value

    def _get_value_for_serialization(self, data, name, spec):
        """ Return the value of the field in entity. """
        name = self.property_name_map[name]
        # todo: remove isintance hack when create() always gives objects
        if self.klass and not isinstance(data, dict):
            return getattr(data, name, None)
        else:
            return data.get(name)

    def _create_mappings(self, spec):
        """ Create property name map based on aliases. """
        ret = dict(zip(set(spec.fields), set(spec.fields)))
        ret.update(dict([(n, s.alias) for n, s in spec.fields.items() if s.alias]))
        return ret


#
#  factory.py ends here
