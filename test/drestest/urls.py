#  -*- coding: utf-8 -*-
# urls.py ---
#
# Created: Wed Dec 14 23:00:19 2011 (+0200)
# Author: Janne Kuuskeri
#


from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',
    url(r'^simple/', include('drestest.simple.urls')),
)


#
# urls.py ends here
