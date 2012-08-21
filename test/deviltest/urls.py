#  -*- coding: utf-8 -*-
# urls.py ---
#
# Created: Wed Dec 14 23:00:19 2011 (+0200)
# Author: Janne Kuuskeri
#


from django.conf.urls.defaults import patterns, include, url

# admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns('',
    url(r'^simple/', include('deviltest.simple.urls')),
    url(r'^docs/', include('deviltest.docs.urls')),
    # uncomment to enable admin:
    # (r'^admin/', include(admin.site.urls)),
)


#
# urls.py ends here
