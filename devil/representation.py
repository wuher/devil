#  -*- coding: utf-8 -*-
# representation.py ---
#
# Created: Tue Feb 21 23:04:38 2011 (+0200)
# Author: Janne Kuuskeri
#


from django import forms
from django.core.exceptions import ValidationError


class Representation(forms.Form):
    """ Base class for Representations.

    Resrouces that want to have automatic data validation may subclass
    this class and define the fields they need. For example::

        class Person(Representation):
            name = forms.CharField(max_length=300)
            age = forms.IntegerField()

    This implementation is based on Django's forms and you should see that
    documentation for details on various fields.

    It should be noted that it is not mandatory to derive your validator
    from this class as long as it implements the ``validate()`` function.
    Moreover, your implementation does not have to depend on Django's forms
    at all.
    """

    def validate(self, data):
        """ Validate the data.

        :returns: validated data. This can be the same data that was given
                  or it can be "cleaned". This implementation uses Django's
                  forms' ``cleaned_data`` property.
        :raises: ValidationError if validation fails.
        """

        spec = self.__class__(data)
        if not spec.is_valid():
            raise ValidationError(spec.errors)
        if len(set(data) - set(spec.fields)) > 0:
            raise ValidationError('too many properties for ' + self.__class__.__name__)
        return spec.cleaned_data


#
# resources.py ends here
