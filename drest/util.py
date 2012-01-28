#  -*- coding: utf-8 -*-
# util.py ---
#
# Created: Fri Dec 30 23:27:52 2011 (+0200)
# Author: Janne Kuuskeri
#


import re


charset_pattern = re.compile('.*;\s*charset=(.*)')


def camelcase_to_slash(name):
    """ Converts CamelCase to camel/case

    code ripped from http://stackoverflow.com/questions/1175208/does-the-python-standard-library-have-function-to-convert-camelcase-to-camel-cas
    """

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1/\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1/\2', s1).lower()

def strip_charset(content_type):
    """ Strip charset from the content type string.

    :param content_type: The Content-Type string (possibly with charset info)
    :returns: The Content-Type string without the charset information
    """

    return content_type.split(';')[0]

def extract_charset(content_type):
    """ Extract charset info from content type.

    E.g.  application/json;charset=utf-8  ->  utf-8

    :param content_type: The Content-Type string (possibly with charset info)
    :returns: The charset or ``None`` if not found.
    """

    match = charset_pattern.match(content_type)
    return match.group(1) if match else None

def get_charset(request):
    """ Extract charset from the content type
    """

    content_type = request.META.get('CONTENT_TYPE', None)
    if content_type:
        return extract_charset(content_type) if content_type else None
    else:
        return None


#
# util.py ends here
