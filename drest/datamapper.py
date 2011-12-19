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


class DataMapper(object):
    content_type = 'text/plain'
    charset = 'utf-8'

    def format(self, request, response, *args, **kw):
        res = self._prepare_response(response)
        res.content = self._format_data(res.content)
        return self._finalize_response(res)

    def parse(self, request, *args, **kw):
        return self._parse_data(request.raw_post_data)

    def _format_data(self, data):
        return data

    def _parse_data(self, data):
        return data

    def _prepare_response(self, response):
        if not isinstance(response, Response):
            return Response(0, response)
        return response

    def _finalize_response(self, response):
        res = HttpResponse(content=response.content,
                           content_type=self._get_content_type())
        # status_code is set separately to allow zero
        res.status_code = response.code
        return res

    def _get_content_type(self):
        return '%s; charset=%s' % (self.content_type, self.charset)



class DefaultMapper(DataMapper):
    def _format_data(self, data):
        return data

    def _parse_data(self, data):
        return data


class JsonMapper(DataMapper):
    content_type = 'application/json'

    def _format_data(self, data):
        return json.dumps(data)

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

    _default_mapper = DefaultMapper()
    _format_query_pattern = re.compile('.*\.(?P<format>\w{1,8})$')
    _datamappers = {
        }

    def register_mapper(self, mapper, content_type, shortname=None):
        """ Register new mapper. """
        self._check_mapper(mapper)
        self._datamappers[content_type] = mapper
        if shortname:
            self._datamappers[shortname] = mapper

    def select_formatter(self, request, *args, **kw):
        mapper_name = self._get_short_name(request, *args, **kw)
        return self._get_mapper(mapper_name)

    def select_parser(self, request, *args, **kw):
        mapper_name = self._get_mapper_name(request, *args, **kw)
        return self._get_mapper(mapper_name)

    def set_default_mapper(self, mapper):
        """ Set the default mapper to be used, when no format is defined.

        If given mapper is None, uses the DefaultMapper.
        """

        if mapper is None:
            self._default_mapper = DefaultMapper()
        else:
            self._check_mapper(mapper)
            self._default_mapper = mapper

    def get_empty_response(self, request, *args, **kw):
        return DataMapper().format(None, '')

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

    def _get_mapper_name(self, request, *args, **kw):
        """ """
        content_type = request.META.get('CONTENT_TYPE', None)

        if not content_type:
            return self._get_short_name(request, *args, **kw)
        else:
            # remove the possible charset-encoding info
            return content_type.split(';')[0]

    def _get_short_name(self, request, *args, **kw):
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

# return default empty response
def get_empty_response(request, *args, **kw):
    return manager.get_empty_response(request, *args, **kw)

# utility function to parse incoming data (selects formatter automatically)
def format(request, response, *args, **kw):
    return manager.select_formatter(request, *args, **kw).format(request, response, *args, **kw)

# utility function to parse incoming data (selects parser automatically)
def parse(request, *args, **kw):
    return manager.select_parser(request, *args, **kw).parse(request, *args, **kw)


#
# datamapper.py ends here
