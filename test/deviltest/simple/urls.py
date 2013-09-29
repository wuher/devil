#  -*- coding: utf-8 -*-
# urls.py ---
#
# Created: Wed Dec 14 23:02:53 2011 (+0200)
# Author: Janne Kuuskeri
#


try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls.defaults import patterns, url
import resources


dictresource = resources.MyDictResource()
textresource = resources.MyTextResource()
respresource = resources.MyRespResource()
authresource = resources.MyAuthResource()
anonresource = resources.MyAnonResource()
permresource = resources.MyPermResource()
noneresource = resources.MyNoneResource()
echoresource = resources.MyEchoResource()
personresource = resources.PersonResource()
mapperresource = resources.MyMapperResource()
decimalresource = resources.MyDecimalResource()
scandicresource = resources.MyScandicResource()
validationresource = resources.MyValidationResource()
scandicjsonresource = resources.MyScandicJsonResource()
defaulttxtmapperresource = resources.MyDefaultMapperResource_1()
defaultobjmapperresource = resources.MyDefaultMapperResource_2()
factoryresource = resources.FactoryResource()


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
    url(r'^person', personresource),
    url(r'^auth/anon', anonresource),
    url(r'^valid', validationresource, name='validation'),
    url(r'^factory', factoryresource),
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
