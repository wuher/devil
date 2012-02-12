#  -*- coding: utf-8 -*-
# resource.py ---
#
# Created: Mon Dec 12 12:10:00 2011 (+0200)
# Author: Janne Kuuskeri
#


import types
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.conf import settings
import errors, datamapper, util
from http import codes
import logging


# todo: move and make configurable
REALM = 'devil'


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
    """ Base class for resources exposed by an API.

    Derive this class to create a resource. At minimum, (in the
    derived class) you need to define one method named after the
    corresponding http method (i.e. post, get, put or delete).

    The response returned by `get()` can be one of the following:
      - django's HttpResponse
      - devil's Response
      - dictionary
      - plaintext

    Additionally, `HttpStatusCodeError`s are caught and converted to
    corresponding http responses.
    """

    # configuration parameters

    access_controller = None
    allow_anonymous = True
    authentication = None
    representation = None
    default_mapper = None
    mapper = None


    def __call__(self, request, *args, **kw):
        """ Entry point for HTTP requests. """

        coerce_put_post(request) #django-fix
        try:
            return self.__handle_request(request, *args, **kw)
        except errors.HttpStatusCodeError, exc:
            return self._get_error_response(exc)
        except Exception, exc:
            return self._get_unknown_error_response(exc)

    def name(self):
        """ Return resource's name.

        This is used mainly by the permission module to determine the
        name of a permission.

        By default, return the name of the class. Override to return
        something else.
        """

        return util.camelcase_to_slash(self.__class__.__name__)

    def __handle_request(self, request, *args, **kw):
        """ Intercept the request and response.

        This function lets `HttpStatusCodeError`s fall through. They
        are caught and transformed into HTTP responses by the caller.

        :return: ``HttpResponse``
        """

        self._authenticate(request)
        self._check_permission(request)
        method = self._get_method(request)
        data = self._get_input_data(request)
        data = self._validate_input_data(data, request)
        response = self._exec_method(method, request, data, *args, **kw)
        formatted_response = self._format_response(request, response)
        self._validate_output_data(response, request, formatted_response)
        return formatted_response

    def _exec_method(self, method, request, data, *args, **kw):
        """ Execute appropriate request handler. """
        if self._is_data_method(request):
            return method(data, request, *args, **kw)
        else:
            return method(request, *args, **kw)

    def _format_response(self, request, response):
        """ Format response.

        If the response is `HttpResponse`, does nothing. Otherwise,
        formats the response using appropriate mapper.

        :param response: resource's response. This can be
           - `None`,
           - django's `HttpResponse`
           - devil's `Response`
           - dictionary (or list of dictionaries)
           - plaintext
        """

        if isinstance(response, HttpResponse):
            return response
        res = datamapper.format(request, response, self)
        # data is now formatted, let's check if the status_code is set
        if res.status_code is 0:
            res.status_code = 200
        # apply headers
        self._add_resposne_headers(res, response)
        return res

    def _add_resposne_headers(self, django_response, devil_response):
        """ Add response headers.

        Add HTTP headers from devil't response to django's response.
        """

        try:
            headers = devil_response.headers
        except AttributeError:
            # ok, there was no devil_response
            pass
        else:
            for k, v in headers.items():
                django_response[k] = v
        return django_response

    def _get_input_data(self, request):
        """ If there is data, parse it, otherwise return None. """
        # only PUT and POST should provide data
        if not self._is_data_method(request):
            return None

        content = [row for row in request.read()]
        content = ''.join(content) if content else None
        return self._parse_input_data(content, request) if content else None

    def _parse_input_data(self, data, request):
        """ Execute appropriate parser. """
        return datamapper.parse(data, request, self)

    def _validate_input_data(self, data, request):
        """ Validate input data.

        :parm request: the HTTP request
        :param data: the parsed data
        :type data: dictionary
        :return: if validation is performed and succeeds the data is converted
                 into whatever format the validation uses (by default Django's
                 Forms) If not, the data is returned unchanged.
        :raises: HttpStatusCodeError if data is not valid
        """

        # when not to validate...
        if not self._is_data_method(request) or not self.representation:
            return data

        def do_validation(item):
            form = self.representation(item)
            if not form.is_valid():
                self._invalid_input_data(data, form)
            return form

        if isinstance(data, (list, tuple)):
            return map(do_validation, data)
        else:
            return do_validation(data)

    def _validate_output_data(self, data, request, response):
        """ Validate the response data.

        :param response: ``HttpResponse``
        :param data: payload data. This implementation assumes
                     dict or list of dicts.
        :raises: `HttpStatusCodeError` if data is not valid
        """

        # when not to validate...
        if response.status_code is not 200 or \
            not self.representation or \
            not data:
            return

        def do_validation(item):
            form = self.representation(item)
            if not form.is_valid():
                self._invalid_output_data(data, form)
            return form

        if isinstance(data, (list, tuple)):
            map(do_validation, data)
        else:
            do_validation(data)

    def _invalid_input_data(self, data, form):
        """ Always raises HttpStatusCodeError.

        Override to raise different status code when request data
        doesn't pass validation.

        todo: should format the content using the datamapper
        """

        raise errors.BadRequest(repr(form.errors))

    def _invalid_output_data(self, data, form):
        """ Always raises HttpStatusCodeError.

        Override to raise different status code when response data
        doesn't pass validation.
        """

        raise errors.InternalServerError()

    def _get_unknown_error_response(self, exc):
        """ Generate HttpResponse for unknown exceptions.

        todo: this should be more informative..
        """

        logging.getLogger('devil').error('devil caught: ' + str(exc), exc_info=True)

        if settings.DEBUG:
            raise
        else:
            return HttpResponse(status=codes.INTERNAL_SERVER_ERROR[1])

    def _get_error_response(self, exc):
        """ Generate HttpResponse based on the HttpStatusCodeError. """
        if exc.has_code(codes.UNAUTHORIZED):
            return self._get_auth_challenge(exc)
        else:
            content = exc.content or ''
            return HttpResponse(content=content, status=exc.get_code_num())

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
        """ Perform authentication. """

        def ensure_user_obj():
            """ Make sure that request object has user property.

            If `request.user` is not present or is `None`, it is
            created and initialized with AnonymousUser.
            """

            try:
                if request.user:
                    return
            except AttributeError:
                pass

            request.user = AnonymousUser()

        def anonymous_access(exc_obj):
            """ Determine what to do with unauthenticated requests.

            If the request has already been authenticated, does
            nothing.

            :param exc_obj: exception object to be thrown if anonymous
            access is not permitted.
            """

            if request.user and request.user.is_authenticated():
                # request is already authenticated
                pass
            elif self.allow_anonymous:
                request.user = AnonymousUser()
            else:
                raise exc_obj

        # first, make sure that the request carries `user` attribute
        ensure_user_obj()
        if self.authentication:
            # authentication handler is configured
            try:
                self.authentication.authenticate(request)
            except errors.Unauthorized, exc:
                # http request doesn't carry any authentication information
                anonymous_access(exc)
        else:
            # no authentication configured
            anonymous_access(errors.Forbidden())

    def _check_permission(self, request):
        """ Check user permissions.

        :raises: Forbidden, if user doesn't have access to the resource.
        """

        if self.access_controller:
            self.access_controller.check_perm(request, self)


#
# resource.py ends here
