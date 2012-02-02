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
noneresource = resources.MyNoneResource()
echoresource = resources.MyEchoResource()
mapperresource = resources.MyMapperResource()
decimalresource = resources.MyDecimalResource()
scandicresource = resources.MyScandicResource()
validationresource = resources.MyValidationResource()
scandicjsonresource = resources.MyScandicJsonResource()
defaulttxtmapperresource = resources.MyDefaultMapperResourceTxt()
defaultobjmapperresource = resources.MyDefaultMapperResourceObj()

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
    url(r'^auth$', authresource),
    url(r'^auth/anon', anonresource),
    url(r'^valid', validationresource),
    url(r'^mapper/dict', dictresource),
    url(r'^mapper/text', textresource),
    url(r'^mapper/resp', respresource),
    url(r'^mapper/none', noneresource),
    url(r'^mapper/echo', echoresource),
    url(r'^mapper/reverse', mapperresource),
    url(r'^mapper/decimal', decimalresource),
    url(r'^mapper/scandic$', scandicresource),
    url(r'^mapper/scandic/json', scandicjsonresource),
    url(r'^mapper/default/txt$', defaulttxtmapperresource),
    url(r'^mapper/default/obj$', defaultobjmapperresource),
)


#
# urls.py ends here
