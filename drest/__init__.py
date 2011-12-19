#  -*- coding: utf-8 -*-
# __init__.py ---
#
# Created: Sat Dec 17 08:38:35 2011 (+0200)
# Author: Janne Kuuskeri
#


import datamapper


def register_mappers():
    jsonmapper = datamapper.JsonMapper()

    # json mapper
    datamapper.manager.register_mapper(jsonmapper, 'application/json', 'json')

    # we'll be tolerant on what we receive
    datamapper.manager.register_mapper(jsonmapper, 'application/x-javascript', 'json')
    datamapper.manager.register_mapper(jsonmapper, 'text/javascript', 'json')
    datamapper.manager.register_mapper(jsonmapper, 'text/x-javascript', 'json')
    datamapper.manager.register_mapper(jsonmapper, 'text/x-json', 'json')

register_mappers()

#
# __init__.py ends here
