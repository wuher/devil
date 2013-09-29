#  -*- coding: utf-8 -*-
# urls.py ---
#
# Created: Wed Dec 14 23:00:19 2011 (+0200)
# Author: Janne Kuuskeri
#


try:
    from django.conf.urls import patterns, url, include
except ImportError:
    from django.conf.urls.defaults import patterns, url, include


# admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^simple/', include('deviltest.simple.urls')),
    url(r'^docs/', include('deviltest.docs.urls')),
    url(r'^doc/', include('devil.docs.urls')),
    # uncomment to enable admin:
    # (r'^admin/', include(admin.site.urls)),
)


#
# urls.py ends here
