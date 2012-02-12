#  -*- coding: utf-8 -*-
# models.py ---
#
# Created: Tue Feb  7 19:37:27 2012 (+0200)
# Author: Janne Kuuskeri
#


from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=10)
    age = models.IntegerField()


#
# models.py ends here
