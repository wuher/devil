#  -*- coding: utf-8 -*-
# representations.py ---
#
# Created: Tue Feb  7 19:44:49 2012 (+0200)
# Author: Janne Kuuskeri
#


from django import forms
from django.core.exceptions import ValidationError
from simple import models


class Person(forms.ModelForm):
    def validate(self, data):
        spec = self.__class__(data)
        if not spec.is_valid():
            raise ValidationError(spec.errors)
        if len(set(data) - set(spec.fields)) > 0:
            raise ValidationError('too many fields')
        return spec.cleaned_data

    id = forms.Field(required=False)

    class Meta:
        model = models.Person


#
# representations.py ends here
