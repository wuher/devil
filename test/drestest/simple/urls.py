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
authresource = resources.MyAuthResource()
anonresource = resources.MyAnonResource()
permresource = resources.MyPermResource()


acl_resources = (
    dictresource,
    textresource,
    respresource,
    authresource,
    anonresource,
    permresource,
    )


urlpatterns = patterns('',
    url(r'^perm', permresource),
    url(r'^auth/anon', anonresource),
    url(r'^auth', authresource),
    url(r'^mapper/dict', dictresource),
    url(r'^mapper/text', textresource),
    url(r'^mapper/resp', respresource),
)


#
# urls.py ends here
