#  -*- coding: utf-8 -*-
#  resource.py ---
#  created: 2012-07-30 09:03:22
#  Author: Janne Kuuskeri
#


from django.core.urlresolvers import get_resolver
from devil import Resource


try:
    # use ordered dict when available
    from collections import OrderedDict as dict
except ImportError:
    pass


class DocumentedResource(Resource):
    """ Base class for all resources that wish to support documentation.

    This class will intercept the incoming request to see whether the client is
    actually requesting a documentation about the resource and not the resource
    itself.

    This class may be subclassed to implement a resource exactly the same way
    as the :class:Resource. Only difference is that the resulting resource
    will return documentation about the resource if the client passes the key
    ``_doc`` in the query string.
    """

    #: these methods are documented
    methods = ('post', 'get', 'put', 'delete',)

    def get_documentation(self, request, *args, **kw):
        """ Generate the documentation. """
        ret = dict()
        ret['resource'] = self.name()
        ret['urls'] = self._get_url_doc()
        ret['description'] = self.__doc__
        ret['representation'] = self._get_representation_doc()
        ret['methods'] = self._get_method_doc()
        return ret

    def _serialize_object(self, response_data, request):
        """ Override to not serialize doc responses. """
        if self._is_doc_request(request):
            return response_data
        else:
            return super(DocumentedResource, self)._serialize_object(
                response_data, request)

    def _validate_output_data(
        self, original_res, serialized_res, formatted_res, request):
        """ Override to not validate doc output. """
        if self._is_doc_request(request):
            return
        else:
            return super(DocumentedResource, self)._validate_output_data(
                original_res, serialized_res, formatted_res, request)

    def _get_method(self, request):
        """ Override to check if this is a documentation request. """
        if self._is_doc_request(request):
            return self.get_documentation
        else:
            return super(DocumentedResource, self)._get_method(request)

    def _is_doc_request(self, request):
        """ Return ``True``, if the client is requesting documentation. """
        return '_doc' in request.GET

    def _get_representation_doc(self):
        """ Return documentation for the representation of the resource. """
        if not self.representation:
            return 'N/A'
        fields = {}
        for name, field in self.representation.fields.items():
            fields[name] = self._get_field_doc(field)
        return fields

    def _get_field_doc(self, field):
        """ Return documentation for a field in the representation. """
        fieldspec = dict()
        fieldspec['type'] = field.__class__.__name__
        fieldspec['required'] = field.required
        fieldspec['validators'] = [{validator.__class__.__name__: validator.__dict__} for validator in field.validators]
        return fieldspec

    def _get_url_doc(self):
        """ Return a list of URLs that map to this resource. """
        resolver = get_resolver(None)
        possibilities = resolver.reverse_dict.getlist(self)
        urls = [possibility[0] for possibility in possibilities]
        return urls

    def _get_method_doc(self):
        """ Return method documentations. """
        ret = {}
        for method_name in self.methods:
            method = getattr(self, method_name, None)
            if method:
                ret[method_name] = method.__doc__
        return ret

#
#  resource.py ends here
