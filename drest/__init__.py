#  -*- coding: utf-8 -*-
# __init__.py ---
#
# Created: Sat Dec 17 08:38:35 2011 (+0200)
# Author: Janne Kuuskeri
#


import parsers


def register_parsers():
    jsonparser = parsers.JsonParser()

    # json parser
    parsers.parsermanager.register_parser(parsers.JsonParser(), 'application/json', 'json')

    # we'll be tolerant on what we receive
    # parsers.parsermanager.register_parser('application/x-javascript': parsers.JsonParser())
    # parsers.parsermanager.register_parser('text/javascript': parsers.JsonParser())
    # parsers.parsermanager.register_parser('text/x-javascript': parsers.JsonParser())
    # parsers.parsermanager.register_parser('text/x-json': parsers.JsonParser())


register_parsers()

#
# __init__.py ends here
