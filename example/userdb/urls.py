#  -*- coding: utf-8 -*-
#  urls.py ---
#  created: 2012-03-13 22:57:28
#

try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls.defaults import patterns, url
from userdb.api import resources

# instantiate resources
user_resource = resources.User()

# define URL mappings to resources
urlpatterns = patterns(
    '',
    url(r'^user/(?P<id>\d{1,4})?', user_resource, name='user'),
)

#
#  urls.py ends here
