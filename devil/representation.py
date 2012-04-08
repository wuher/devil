#  -*- coding: utf-8 -*-
# representation.py ---
#
# Created: Tue Feb 21 23:04:38 2011 (+0200)
# Author: Janne Kuuskeri
#


from django import forms
from django.core.exceptions import ValidationError


class Representation(forms.Form):
    def validate(self, data):
        spec = self.__class__(data)
        if not spec.is_valid():
            raise ValidationError(spec.errors)
        if len(set(data) - set(spec.fields)) > 0:
            raise ValidationError('too many properties for ' + self.__class__.__name__)
        return spec.cleaned_data


#
# resources.py ends here
