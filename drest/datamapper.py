#  -*- coding: utf-8 -*-
# datamapper.py ---
#
# Created: Thu Dec 15 10:03:04 2011 (+0200)
# Author: Janne Kuuskeri
#


import re, json
from django.http import HttpResponse
import errors
from http import Response
import util


class DataMapper(object):
    content_type = 'text/plain'
    charset = 'utf-8'

    def format(self, request, response):
        """ Format the data.

        It is usually a better idea to override `_format_data()` than
        this method in derived classes.

        @param response drests's `Response` object or the data
        itself. May also be `None`.
        """
        res = self._prepare_response(response)
        res.content = self._format_data(res.content)
        return self._finalize_response(res)

    def parse(self, request):
        """ Parse the data.

        It is usually a better idea to override `_parse_data()` than
        this method in derived classes.

        @param request either `HttpRequest` or the data itself.
        """

        try:
            data = request.raw_post_data
        except AttributeError:
            # no raw_post_data, maybe the parameter is the data
            data = request
        return self._parse_data(data)

    def _format_data(self, data):
        """ Format the data

        @param data the data (may be None)
        """

        return data if data is not None else ''

    def _parse_data(self, data):
        """ Parse the data

        @param data the data
        """

        return data

    def _prepare_response(self, response):
        """ Coerce response to drest's Response

        @return Response
        """

        if not isinstance(response, Response):
            return Response(0, response)
        return response

    def _finalize_response(self, response):
        res = HttpResponse(content=response.content,
                           content_type=self._get_content_type())
        # status_code is set separately to allow zero
        res.status_code = response.code
        return res

    def _get_empty_format(self):
        """ Override to provide something else for empty responses. """
        return ''

    def _get_content_type(self):
        return '%s; charset=%s' % (self.content_type, self.charset)


class JsonMapper(DataMapper):
    content_type = 'application/json'

    def _format_data(self, data):
        return json.dumps(data) if data is not None else ''

    def _parse_data(self, data):
        try:
            return json.loads(data)
        except ValueError:
            raise errors.BadRequest('unable to parse data')


class DataMapperManager(object):
    """ DataMapperManager tries to parse and format payload data when
    possible.

    First, try to figure out the content-type of the data, then find
    corresponding mapper and parse/format the data. If no mapper is
    registered or the content-type can't be determined, does nothing.

    Forllowing order is used when determining the content-type.
    1. Content-Type HTTP header
    2. "format" query parameter (e.g. ?format=json)
    3. file-extension in the requestd URL (e.g. /user.json)
    """

    _default_mapper = DataMapper()
    _format_query_pattern = re.compile('.*\.(?P<format>\w{1,8})$')
    _datamappers = {
        }

    def register_mapper(self, mapper, content_type, shortname=None):
        """ Register new mapper. """
        self._check_mapper(mapper)
        self._datamappers[content_type] = mapper
        if shortname:
            self._datamappers[shortname] = mapper

    def select_formatter(self, request):
        mapper_name = self._get_short_name(request)
        return self._get_mapper(mapper_name)

    def select_parser(self, request):
        mapper_name = self._get_mapper_name(request)
        return self._get_mapper(mapper_name)

    def get_mapper_by_content_type(self, content_type):
        content_type = util.strip_charset(content_type)
        return self._get_mapper(content_type)

    def set_default_mapper(self, mapper):
        """ Set the default mapper to be used, when no format is defined.

        If given mapper is None, uses the `DataMapper`.
        """

        if mapper is None:
            self._default_mapper = DataMapper()
        else:
            self._check_mapper(mapper)
            self._default_mapper = mapper

    def _get_mapper(self, mapper_name):
        """ Select appropriate mapper for the incoming data. """
        if not mapper_name:
            # unspecified -> use default
            return self._get_default_mapper()
        elif not mapper_name in self._datamappers:
            # unknown
            return self._unknown_format(mapper_name)
        else:
            # mapper found
            return self._datamappers[mapper_name]

    def _get_mapper_name(self, request):
        """ """
        content_type = request.META.get('CONTENT_TYPE', None)

        if not content_type:
            return self._get_short_name(request)
        else:
            # remove the possible charset-encoding info
            return util.strip_charset(content_type)

    def _get_short_name(self, request):
        """ """
        format = request.GET.get('format', None)
        if not format:
            match = self._format_query_pattern.match(request.path)
            if match and match.group('format'):
                format = match.group('format')
        return format

    def _get_default_mapper(self):
        """ """
        return self._default_mapper

    def _unknown_format(self, format):
        """ """
        raise errors.NotAcceptable('unknown data format: ' + format)

    def _check_mapper(self, mapper):
        """ Check that the mapper has valid signature. """
        if not hasattr(mapper, 'parse') or not callable(mapper.parse):
            raise ValueError('mapper must implement parse()')
        if not hasattr(mapper, 'format') or not callable(mapper.format):
            raise ValueError('mapper must implement format()')


# singleton instance
manager = DataMapperManager()

# utility function to parse incoming data (selects formatter automatically)
def format(request, response):
    return manager.select_formatter(request).format(request, response)

# utility function to parse incoming data (selects parser automatically)
def parse(request):
    return manager.select_parser(request).parse(request)


#
# datamapper.py ends here
