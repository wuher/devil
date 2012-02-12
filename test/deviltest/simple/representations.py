#  -*- coding: utf-8 -*-
# representations.py ---
#
# Created: Tue Feb  7 19:44:49 2012 (+0200)
# Author: Janne Kuuskeri
#


from django.forms import ModelForm
from simple import models


class Person(ModelForm):
    class Meta:
        model = models.Person


#
# representations.py ends here
