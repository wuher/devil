#  -*- coding: utf-8 -*-
# util.py ---
#
# Created: Fri Dec 30 23:27:52 2011 (+0200)
# Author: Janne Kuuskeri
#


import re


charset_pattern = re.compile('.*;\s*charset=(.*)')


def strip_charset(content_type):
    return content_type.split(';')[0]

def extract_charset(content_type):
    """ Extract charset info from content type.

    E.g.  application/json;charset=utf-8  ->  utf-8
    """
    try:
        match = charset_pattern.match(content_type)
    except TypeError:
        # content_type was most likely None
        return None
    else:
        return match.group(1) if match else None

def get_charset(request):
    content_type = request.META.get('CONTENT_TYPE', None)
    return extract_charset(content_type) if content_type else None


#
# util.py ends here
