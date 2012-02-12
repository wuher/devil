#  -*- coding: utf-8 -*-
# jsonmapper.py ---
#
# Created: Fri Feb  3 12:41:46 2012 (+0200)
# Author: Janne Kuuskeri
#


import simplejson as json
from devil.datamapper import DataMapper
from devil import errors


class JsonMapper(DataMapper):
    content_type = 'application/json'

    def __init__(self, use_decimal=False):
        """ Initialize JSON mapper with appropriate use of numbers.

        :param use_decimal: ``True`` if numbers should be converted into ``Decimal``s
        """

        self.use_decimal = use_decimal

    def _format_data(self, data, charset):
        if data is None or data == '':
            return u''
        else:
            params = {
                'indent': 4,
                'ensure_ascii': False,
                'encoding': charset,
                }
            self._maybe_add_use_decimal(params)
            return json.dumps(data, **params)

    def _parse_data(self, data, charset):
        params = {}
        self._maybe_add_use_decimal(params)
        try:
            return json.loads(data, charset, **params)
        except ValueError:
            raise errors.BadRequest('unable to parse data')

    def _maybe_add_use_decimal(self, params):
        """ Maybe add ``use_decimal`` to the given parameters

        obviously it's different to say use_decimal=False than
        it is to leave it out completely..
        """

        if self.use_decimal:
            params['use_decimal'] = True

#
# jsonmapper.py ends here
