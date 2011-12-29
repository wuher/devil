#  -*- coding: utf-8 -*-
# RouteResource.py ---
#
# Created: Mon Dec 12 13:49:22 2011 (+0200)
# Author: Janne Kuuskeri
#


from drest.resource import Resource


class RouteResource(Resource):

    access_control = True

    def get(self, request, *args, **kw):
        route_id = int(kw['route'])
        route = route_repo.get_route(route_id)
        return route


#
# RouteResource.py ends here
