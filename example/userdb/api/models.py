#  -*- coding: utf-8 -*-
#  models.py ---
#  created: 2012-03-13 23:08:13
#


from django.db import models


class User(models.Model):
    name = models.CharField(max_length=60)
    age = models.IntegerField()

    class Meta:
        db_table = 'user'


#
#  models.py ends here
