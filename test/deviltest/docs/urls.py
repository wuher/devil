#  -*- coding: utf-8 -*-
#  urls.py ---
#  created: 2012-07-30 08:14:41
#  Author: Janne Kuuskeri
#


from django.conf.urls.defaults import patterns, url
from . import resources


first = resources.MyTestResource()


urlpatterns = patterns('',
    url(r'^first/(?P<first_id>\d{1,7})?$', first),
    )


#
#  urls.py ends here
