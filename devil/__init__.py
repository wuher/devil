#  -*- coding: utf-8 -*-
# __init__.py ---
#
# Created: Sat Dec 17 08:38:35 2011 (+0200)
# Author: Janne Kuuskeri
#


import logging, sys
import datamapper
from mappers.xmlmapper import XmlMapper
from mappers.jsonmapper import JsonMapper


def init_logging():
    log = logging.getLogger('devil')
    if log.level == logging.NOTSET:
        log.setLevel(logging.WARN)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'))
        log.addHandler(handler)

def register_mappers():
    textmapper = datamapper.DataMapper()
    jsonmapper = JsonMapper()
    xmlmapper = XmlMapper(numbermode='basic')

    # we'll be tolerant on what we receive
    # remember to put these false content types in the beginning so that they
    # are overridden by the proper ones
    datamapper.manager.register_mapper(jsonmapper, 'application/x-javascript', 'json')
    datamapper.manager.register_mapper(jsonmapper, 'text/javascript', 'json')
    datamapper.manager.register_mapper(jsonmapper, 'text/x-javascript', 'json')
    datamapper.manager.register_mapper(jsonmapper, 'text/x-json', 'json')

    # text mapper
    datamapper.manager.register_mapper(textmapper, 'text/plain', 'text')

    # xml mapper
    datamapper.manager.register_mapper(xmlmapper, 'text/xml', 'xml')

    # json mapper
    datamapper.manager.register_mapper(jsonmapper, 'application/json', 'json')

init_logging()
register_mappers()

#
# __init__.py ends here
