#  -*- coding: utf-8 -*-
#  resources.py ---
#  created: 2012-03-13 22:16:15
#


from django.core.urlresolvers import reverse
from django.db import DatabaseError
from devil.resource import Resource
from devil.mappers.jsonmapper import JsonMapper
from devil.http import Response
from devil import errors
from userdb.api import models


class User(Resource):

    # if client doesn't specify mimetype, assume JSON
    default_mapper = JsonMapper()

    def post(self, data, request, id):
        """ Create a new resource using POST """
        if id:
            # can't post to individual user
            raise errors.MethodNotAllowed()
        user = self._dict_to_model(data)
        user.save()
        # according to REST, return 201 and Location header
        return Response(201, None, {
            'Location': '%s%d' % (reverse('user'), user.pk)})

    def get(self, request, id):
        """ Get one user or all users """
        if id:
            return self._get_one(id)
        else:
            return self._get_all()

    def put(self, data, request, id):
        """ Update a single user. """
        if not id:
            # can't update the whole container
            raise errors.MethodNotAllowed()
        userdata = self._dict_to_model(data)
        userdata.pk = id
        try:
            userdata.save(force_update=True)
        except DatabaseError:
            # can't udpate non-existing user
            raise errors.NotFound()

    def delete(self, request, id):
        """ Delete a single user. """
        if not id:
            # can't delete the whole container
            raise errors.MethodNotAllowed()
        try:
            models.User.objects.get(pk=id).delete()
        except models.User.DoesNotExist:
            # we never had it, so it's definitely deleted
            pass

    def _get_one(self, id):
        """ Get one user from db and turn into dict """
        try:
            return self._to_dict(models.User.objects.get(pk=id))
        except models.User.DoesNotExist:
            raise errors.NotFound()

    def _get_all(self):
        """ Get all users from db and turn into list of dicts """
        return [self._to_dict(row) for row in models.User.objects.all()]

    def _to_dict(self, row):
        """ Convert a single user db row into dict. """
        return {
            'name': row.name,
            'age': row.age,
        }

    def _dict_to_model(self, data):
        """ Create new user model instance based on the received data.

        Note that the created user is not saved into database.
        """

        try:
            # we can do this because we have same fields
            # in the representation and in the model:
            user = models.User(**data)
        except TypeError:
            # client sent bad data
            raise errors.BadRequest()
        else:
            return user

#
#  resources.py ends here
