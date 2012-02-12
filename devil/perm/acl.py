#  -*- coding: utf-8 -*-
# acl.py ---
#
# Created: Wed Dec 21 16:43:05 2011 (+0200)
# Author: Janne Kuuskeri
#


from devil import errors


class PermissionController(object):
    """ Permission based access conttoller. """

    PREFIX = 'resource'
    METHODS = ('post', 'get', 'put', 'delete')

    @classmethod
    def get_perm_names(cls, resource):
        """ Return all permissions supported by the resource.

        This is used for auto-generating missing permissions rows into
        database in syncdb.
        """

        return [cls.get_perm_name(resource, method) for method in cls.METHODS]

    @classmethod
    def get_perm_name(cls, resource, method):
        """ Compose permission name

        @param resource the resource
        @param method the request method (case doesn't matter).
        """

        return '%s_%s_%s' % (
            cls.PREFIX,
            cls._get_resource_name(resource),
            method.lower())

    def check_perm(self, request, resource):
        """ Check permission

        @param request the HTTP request
        @param resource the requested resource
        @raise Forbidden if the user doesn't have access to the resource
        """

        perm_name = self.get_perm_name(resource, request.method)
        if not self._has_perm(request.user, perm_name):
            raise errors.Forbidden()

    def _has_perm(self, user, permission):
        """ Check whether the user has the given permission

        @return True if user is granted with access, False if not.
        """

        if user.is_superuser:
            return True
        if user.is_active:
            perms = [perm.split('.')[1] for perm in user.get_all_permissions()]
            return permission in perms
        return False

    @classmethod
    def _get_resource_name(self, resource):
        """ Return the name of the resource.

        This is a separate method to make it easier to define a different
        way to define the name in a derived class.
        """

        return resource.name()


#
# acl.py ends here
