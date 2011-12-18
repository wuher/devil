#  -*- coding: utf-8 -*-
# urls.py ---
#
# Created: Wed Dec 14 23:02:53 2011 (+0200)
# Author: Janne Kuuskeri
#


from django.conf.urls.defaults import patterns, include, url
from drest.resource import Resource
import resources


testresource = resources.MyTestResource()

urlpatterns = patterns('',
    url(r'^test/', testresource),
)


#
# urls.py ends here
