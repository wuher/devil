#  -*- coding: utf-8 -*-
# resource.py ---
#
# Created: Mon Dec 12 12:10:00 2011 (+0200)
# Author: Janne Kuuskeri
#


from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
import errors, datamapper
from http import codes


# todo: move and make configurable
REALM = "test"


# todo: move somewhere and add note about borrowing this from piston
def coerce_put_post(request):
    """
    Django doesn't particularly understand REST.
    In case we send data over PUT, Django won't
    actually look at the data and load it. We need
    to twist its arm here.

    The try/except abominiation here is due to a bug
    in mod_python. This should fix it.
    """
    if request.method.upper() == "PUT":
        # Bug fix: if _load_post_and_files has already been called, for
        # example by middleware accessing request.POST, the below code to
        # pretend the request is a POST instead of a PUT will be too late
        # to make a difference. Also calling _load_post_and_files will result
        # in the following exception:
        #   AttributeError: You cannot set the upload handlers after the upload has been processed.
        # The fix is to check for the presence of the _post field which is set
        # the first time _load_post_and_files is called (both by wsgi.py and
        # modpython.py). If it's set, the request has to be 'reset' to redo
        # the query value parsing in POST mode.
        if hasattr(request, '_post'):
            del request._post
            del request._files

        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'

        request.PUT = request.POST


class Resource(object):

    use_access_control = False
    allow_empty_data = True
    authentication = None
    presentation = None
    parameters = None
    formatter = None
    parser = None


    def __call__(self, request, *args, **kw):
        """ Entry point for HTTP requests. """
        coerce_put_post(request) #django-fix
        try:
            return self._handle_request(request, *args, **kw)
        except errors.HttpStatusCodeError, e:
            return self._get_error_response(e)

    def _handle_request(self, request, *args, **kw):
        """  """
        user = self._authenticate(request)
        method = self._get_method(request)
        data = self._get_input_data(request, *args, **kw)
        # params = self._get_input_params(request, *args, **kw)
        response = self._exec_method(method, request, data, *args, **kw)
        response = self._format_response(request, response, *args, **kw)
        return response

    def _exec_method(self, method, request, data, *args, **kw):
        """ """
        if self._is_data_method(request):
            return method(data, request, *args, **kw)
        else:
            return method(request, *args, **kw)

    def _format_response(self, request, response, *args, **kw):
        """ """
        if response is None:
            res = datamapper.get_empty_response(request, *args, **kw)
        elif isinstance(response, HttpResponse):
            res = response
        else:
            res = datamapper.format(request, response, *args, **kw)
        if res.status_code is 0:
            res.status_code = 200
        return res

    def _get_input_data(self, request, *args, **kw):
        """ If there is data, parse it, otherwise return None. """
        # only PUT and POST should provide data
        if not self._is_data_method(request):
            return None

        if request.raw_post_data:
            return self._parse_data(request, *args, **kw)
        elif not self.allow_empty_data:
            raise errors.BadRequest('no data provided')
        else:
            # no data provided, but that's ok
            return None

    def _parse_data(self, request, *args, **kw):
        """ Execute appropriate parser """
        if self.parser:
            return self.parser(request, *args, **kw)
        else:
            return datamapper.parse(request, *args, **kw)

    def _get_error_response(self, exc):
        """ Generate HttpResponse based on the HttpStatusCodeError. """
        if exc.has_code(codes.UNAUTHORIZED):
            return self._get_auth_challenge(exc)
        else:
            return HttpResponse(content=exc.content, status=exc.get_code_num())

    def _get_auth_challenge(self, exc):
        """ Returns HttpResponse for the client. """
        response = HttpResponse(content=exc.content, status=exc.get_code_num())
        response['WWW-Authenticate'] = 'Basic realm="%s"' % REALM
        return response

    def _get_method(self, request):
        """ Figure out the requested method and return the callable. """
        methodname = request.method.lower()
        method = getattr(self, methodname, None)
        if not method or not callable(method):
            raise errors.MethodNotAllowed()
        return method

    def _is_data_method(self, request):
        """ Return True, if request method is either PUT or POST """
        return request.method.upper() in ('PUT', 'POST')

    def _authenticate(self, request):
        if self.authentication:
            return self.authentication.authenticate(request)
        else:
            return AnonymousUser()

#
# resource.py ends here
