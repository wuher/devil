#  -*- coding: utf-8 -*-
# datamapper.py ---
#
# Created: Thu Dec 15 10:03:04 2011 (+0200)
# Author: Janne Kuuskeri
#


import re
from decimal import Decimal, InvalidOperation
from django.utils.encoding import smart_unicode, smart_str
from django.http import HttpResponse
import errors
from http import Response
import util


class DataMapper(object):
    """ Base class for all data mappers.

    This class also implements ``text/plain`` datamapper.
    """

    content_type = 'text/plain'
    charset = 'utf-8'

    def format(self, response):
        """ Format the data.

        In derived classed, it is usually better idea to override
        ``_format_data()`` than this method.

        :param response: devil's ``Response`` object or the data
                         itself. May also be ``None``.
        :return: django's ``HttpResponse``
        """

        res = self._prepare_response(response)
        res.content = self._format_data(res.content, self.charset)
        return self._finalize_response(res)

    def parse(self, data, charset=None):
        """ Parse the data.

        It is usually a better idea to override ``_parse_data()`` than
        this method in derived classes.

        :param charset: the charset of the data. Uses datamapper's
        default (``self.charset``) if not given.
        :returns:
        """

        charset = charset or self.charset
        return self._parse_data(data, charset)

    def _decode_data(self, data, charset):
        """ Decode string data.

        :returns: unicode string
        """

        try:
            return smart_unicode(data, charset)
        except UnicodeDecodeError:
            raise errors.BadRequest('wrong charset')

    def _encode_data(self, data):
        """ Encode string data. """
        return smart_str(data, self.charset)

    def _format_data(self, data, charset):
        """ Format the data

        @param data the data (may be None)
        """

        return self._encode_data(data) if data else u''

    def _parse_data(self, data, charset):
        """ Parse the data

        :param data: the data (may be None)
        """

        return self._decode_data(data, charset) if data else u''

    def _prepare_response(self, response):
        """ Coerce response to devil's Response

        :param response: either the response data or a ``Response`` object.
        :returns: ``Response`` object
        """

        if not isinstance(response, Response):
            return Response(0, response)
        return response

    def _finalize_response(self, response):
        """ Convert the ``Response`` object into django's ``HttpResponse``

        :return: django's ``HttpResponse``
        """

        res = HttpResponse(content=response.content,
                           content_type=self._get_content_type())
        # status_code is set separately to allow zero
        res.status_code = response.code
        return res

    def _get_content_type(self):
        """ Return Content-Type header with charset info. """
        return '%s; charset=%s' % (self.content_type, self.charset)


class DataMapperManager(object):
    """ This class finds the appropriate mapper for the request/response.

    First, tries to figure out the content-type of the data, then find
    corresponding mapper and parse/format the data. If no mapper is
    registered or the content-type can't be determined, does nothing.

    Following order is used when determining the content-type.
    1. Content-Type HTTP header (for parsing only)
    2. "format" query parameter (e.g. ?format=json)
    3. file-extension in the requestd URL (e.g. /user.json)
    4. HTTP Accept header (for formatting only)
    """

    _format_query_pattern = re.compile('.*\.(?P<format>\w{1,8})$')
    _datamappers = {}

    def __init__(self):
        """ Initialize the manager.

        The ``_datamappers`` dictianary is initialized here to make testing easier.
        """

        self._datamappers = {
            '*/*': DataMapper()
            }

    def register_mapper(self, mapper, content_type, shortname=None):
        """ Register new mapper.

        :param mapper: mapper object needs to implement ``parse()`` and
        ``format()`` functions.
        """

        self._check_mapper(mapper)
        cont_type_names = self._get_content_type_names(content_type, shortname)
        self._datamappers.update(dict([(name, mapper) for name in cont_type_names]))

    def select_formatter(self, request, resource):
        """ Select appropriate formatter based on the request.

        :param request: the HTTP request
        :param resource: the invoked resource
        """

        # 1. get from resource
        if resource.mapper:
            return resource.mapper
        # 2. get from url
        mapper_name = self._get_name_from_url(request)
        if mapper_name:
            return self._get_mapper(mapper_name)
        # 3. get from accept header
        mapper_name = self._get_name_from_accept(request)
        if mapper_name:
            return self._get_mapper(mapper_name)
        # 4. use resource's default
        if resource.default_mapper:
            return resource.default_mapper
        # 5. use manager's default
        return self._get_default_mapper()

    def select_parser(self, request, resource):
        """ Select appropriate parser based on the request.

        :param request: the HTTP request
        :param resource: the invoked resource
        """

        # 1. get from resource
        if resource.mapper:
            return resource.mapper
        # 2. get from content type
        mapper_name = self._get_name_from_content_type(request)
        if mapper_name:
            return self._get_mapper(mapper_name)
        # 3. get from url
        mapper_name = self._get_name_from_url(request)
        if mapper_name:
            return self._get_mapper(mapper_name)
        # 4. use resource's default
        if resource.default_mapper:
            return resource.default_mapper
        # 5. use manager's default
        return self._get_default_mapper()

    def get_mapper_by_content_type(self, content_type):
        """ Returs mapper based on the content type. """

        content_type = util.strip_charset(content_type)
        return self._get_mapper(content_type)

    def set_default_mapper(self, mapper):
        """ Set the default mapper to be used, when no format is defined.

        This is the same as calling ``register_mapper`` with ``*/*`` with the
        exception of giving ``None`` as parameter.

        :param mapper: the mapper. If None, uses ``DataMapper``.
        """

        mapper = mapper or DataMapper()
        self._datamappers['*/*'] = mapper

    def _get_default_mapper(self):
        """ Return the default mapper.

        This is the mapper that response to ``Content-Type: */*``.
        """

        return self._datamappers['*/*']

    def _get_mapper(self, mapper_name):
        """ Return the mapper based on the given name.

        :returns: the mapper based on the given ``mapper_name``
        :raises: NotAcceptable if we don't support the requested format.
        """

        if mapper_name in self._datamappers:
            # mapper found
            return self._datamappers[mapper_name]
        else:
            # unsupported format
            return self._unknown_format(mapper_name)

    def _get_name_from_content_type(self, request):
        """ Get name from Content-Type header """

        content_type = request.META.get('CONTENT_TYPE', None)
        if content_type:
            # remove the possible charset-encoding info
            return util.strip_charset(content_type)
        return None

    def _get_name_from_accept(self, request):
        """ Process the Accept HTTP header.

        Find the most suitable mapper that the client wants and we support.

        :returns: the preferred mapper based on the accept header or ``None``.
        """

        accepts = util.parse_accept_header(request.META.get("HTTP_ACCEPT", ""))
        if not accepts:
            return None

        for accept in accepts:
            if accept[0] in self._datamappers:
                return accept[0]
        raise errors.NotAcceptable()

    def _get_name_from_url(self, request):
        """ Determine short name for the mapper based on the URL.

        Short name can be either in query string (e.g. ?format=json)
        or as an extension to the URL (e.g. myresource.json).

        :returns: short name of the mapper or ``None`` if not found.
        """

        format = request.GET.get('format', None)
        if not format:
            match = self._format_query_pattern.match(request.path)
            if match and match.group('format'):
                format = match.group('format')
        return format

    def _unknown_format(self, format):
        """ Deal with the situation when we don't support the requested format.

        :raises: NotAcceptable always
        """

        raise errors.NotAcceptable('unknown data format: ' + format)

    def _get_content_type_names(self, content_type, shortname):
        """ """
        ret = [shortname, content_type] if shortname else [content_type]

        mtype, subtype = content_type.split('/', 1)
        if mtype != '*' and subtype != '*':
            ret.append('%s/*' % (mtype,))
        return ret

    def _check_mapper(self, mapper):
        """ Check that the mapper has valid signature. """
        if not hasattr(mapper, 'parse') or not callable(mapper.parse):
            raise ValueError('mapper must implement parse()')
        if not hasattr(mapper, 'format') or not callable(mapper.format):
            raise ValueError('mapper must implement format()')


# singleton instance
manager = DataMapperManager()

# utility function to format outgoing data (selects formatter automatically)
def format(request, response, resource):
    return manager.select_formatter(request, resource).format(response)

# utility function to parse incoming data (selects parser automatically)
def parse(data, request, resource):
    charset = util.get_charset(request)
    return manager.select_parser(request, resource).parse(data, charset)


#
# datamapper.py ends here
