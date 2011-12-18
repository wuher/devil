#  -*- coding: utf-8 -*-
# parsers.py ---
#
# Created: Thu Dec 15 10:03:04 2011 (+0200)
# Author: Janne Kuuskeri
#


import re, json
import errors


class Parser(object):
    def parse(self, request, *args, **kw):
        pass


class DefaultParser(object):
    def parse(self, request, *args, **kw):
        return request.raw_post_data


class JsonParser(Parser):
    def parse(self, request, *args, **kw):
        if not request.raw_post_data:
            raise errors.BadRequest('no data given')
        try:
            return json.loads(request.raw_post_data)
        except ValueError:
            raise errors.BadRequest('unable to parse data')


class ParserManager(object):
    """ ParserManager tries to parse client's data when possible.

    First, try to figure out the content-type of the data, then find
    corresponding parser and parse the data. If no parser is
    registered or the content-type can't be determined, does nothing.

    Forllowing order is used when determining the content-type.
    1. Content-Type HTTP header
    2. "format" query parameter (e.g. ?format=json)
    3. file-extension in the requestd URL (e.g. /user.json)
    """

    format_query_pattern = re.compile('.*\.(?P<format>\w{1,8})$')
    parsermap = {
        }

    def register_parser(self, parser, content_type, shortname=None):
        """ Register new parser. """
        if not parser or not hasattr(parser, 'parse') or not callable(parser.parse):
            raise ValueError('parser must implement parse()')
        self.parsermap[content_type] = parser
        if shortname:
            self.parsermap[shortname] = parser

    def select_parser(self, request, *args, **kw):
        """ Select appropriate parser for the incoming data. """
        parser_name = self._get_parser_name(request, *args, **kw)
        if not parser_name:
            # unspecified -> use default
            return self._get_default_parser()
        elif not parser_name in self.parsermap:
            # unknown
            return self._unknown_format(parser_name)
        else:
            # parser found
            return self.parsermap[parser_name]

    def _get_parser_name(self, request, *args, **kw):
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
            match = self.format_query_pattern.match(request.path)
            if match and match.group('format'):
                format = match.group('format')
        return format

    def _get_default_parser(self):
        """ """
        return DefaultParser()

    def _unknown_format(self, format):
        """ """
        raise errors.BadRequest('unknown data format: ' + format)


# singleton instance
parsermanager = ParserManager()

# utility function. by default, this is the only public function you need.
def parse(request, *args, **kw):
    return parsermanager.select_parser(request, *args, **kw).parse(request, *args, **kw)


#
# parsers.py ends here
