#  -*- coding: utf-8 -*-
# urls.py ---
#
# Created: Wed Dec 14 23:02:53 2011 (+0200)
# Author: Janne Kuuskeri
#


from django.conf.urls.defaults import patterns, include, url
from drest.resource import Resource
import resources


dictresource = resources.MyDictResource()
textresource = resources.MyTextResource()
respresource = resources.MyRespResource()

urlpatterns = patterns('',
    url(r'^mapper/dict', dictresource),
    url(r'^mapper/text', textresource),
    url(r'^mapper/resp', respresource),
)


#
# urls.py ends here
