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


def parse_accept_header(accept):
    """ Parse the Accept header

    todo: memoize

    :returns: list with pairs of (media_type, q_value), ordered by q
    values.
    """

    def parse_media_range(accept_item):
        """ Parse media range and subtype """

        return accept_item.split('/', 1)

    def comparator(a, b):
        """ Compare accept items a and b """

        # first compare q values
        result = -cmp(a[2], b[2])
        if result is not 0:
            # q values differ, no need to compare media types
            return result

        # parse media types and compare them (asterisks are lower in precedence)
        mtype_a, subtype_a = parse_media_range(a[0])
        mtype_b, subtype_b = parse_media_range(b[0])
        if mtype_a == '*' and subtype_a == '*':
            return 1
        if mtype_b == '*' and subtype_b == '*':
            return -1
        if subtype_a == '*':
            return 1
        if subtype_b == '*':
            return -1
        return 0

    if not accept:
        return []

    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0).strip()
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(comparator)
    return result

#
# util.py ends here
