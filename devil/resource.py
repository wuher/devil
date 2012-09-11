#  -*- coding: utf-8 -*-
# resource.py ---
#
# Created: Mon Dec 12 12:10:00 2011 (+0200)
# Author: Janne Kuuskeri
#


from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.conf import settings
import errors
import datamapper
import util
from http import codes, Response
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

    See the documentation on ``_process_response()`` to see what can
    be returned by this method. Additionally, ``HttpStatusCodeError``s
    are caught and converted to corresponding http responses.

    todo: change function parameters so that request is always before response.
    """

    # configuration parameters

    access_controller = None
    allow_anonymous = True
    authentication = None
    representation = None
    post_representation = None
    factory = None
    post_factory = None
    default_mapper = None
    mapper = None

    def __call__(self, request, *args, **kw):
        """ Entry point for HTTP requests. """

        coerce_put_post(request)  # django-fix
        try:
            return self.__handle_request(request, *args, **kw)
        except errors.HttpStatusCodeError, exc:
            return self._get_error_response(exc)
        except Exception, exc:
            return self._get_unknown_error_response(request, exc)

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
        data = self._clean_input_data(data, request)
        response = self._exec_method(method, request, data, *args, **kw)
        return self._process_response(response, request)

    def _exec_method(self, method, request, data, *args, **kw):
        """ Execute appropriate request handler. """
        if self._is_data_method(request):
            return method(data, request, *args, **kw)
        else:
            return method(request, *args, **kw)

    def _process_response(self, response, request):
        """ Process the response.

        If the response is ``HttpResponse``, does nothing. Otherwise,
        serializes, formats and validates the response.

        :param response: resource's response. This can be
           - ``None``,
           - django's ``HttpResponse``
           - devil's ``Response``
           - dictionary (or list of dictionaries)
           - object (or list of objects) that are first serialized into dict
             using ``self.factory``.
           - plaintext
        :returns: Django's ``HttpResponse``
        """

        def coerce_response():
            """ Coerce the response object into devil structure. """
            if not isinstance(response, Response):
                return Response(0, response)
            return response

        if isinstance(response, HttpResponse):
            # we don't do anything if resource returns django's http response
            return response

        devil_res = coerce_response()
        if devil_res.content and devil_res.get_code_num() in (0, 200, 201):
            # serialize, format and validate
            serialized_res = devil_res.content = self._serialize_object(devil_res.content, request)
            formatted_res = self._format_response(request, devil_res)
            self._validate_output_data(response, serialized_res, formatted_res, request)
        else:
            # no data -> format only
            formatted_res = self._format_response(request, devil_res)
        return formatted_res

    def _format_response(self, request, response):
        """ Format response using appropriate datamapper.

        Take the devil response and turn it into django response, ready to
        be returned to the client.
        """

        res = datamapper.format(request, response, self)
        # data is now formatted, let's check if the status_code is set
        if res.status_code is 0:
            res.status_code = 200
        # apply headers
        self._add_resposne_headers(res, response)
        return res

    def _add_resposne_headers(self, django_response, devil_response):
        """ Add response headers.

        Add HTTP headers from devil's response to django's response.
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

    def _clean_input_data(self, data, request):
        """ Clean input data. """

        # sanity check
        if not self._is_data_method(request):
            # this is not PUT or POST -> return
            return data

        # do cleaning
        try:
            if self.representation:
                # representation defined -> perform validation
                self._validate_input_data(data, request)
            if self.factory:
                # factory defined -> create object
                return self._create_object(data, request)
            else:
                # no factory nor representation -> return the same data back
                return data
        except ValidationError, exc:
            return self._input_validation_failed(exc, data, request)

    def _get_input_validator(self, request):
        """ Return appropriate input validator.

        For POST requests, ``self.post_representation`` is returned
        if it is present, ``self.representation`` otherwise.
        """

        method = request.method.upper()
        if method != 'POST':
            return self.representation
        elif self.post_representation:
            return self.post_representation
        else:
            return self.representation

    def _validate_input_data(self, data, request):
        """ Validate input data.

        :param request: the HTTP request
        :param data: the parsed data
        :type data: dictionary
        :return: if validation is performed and succeeds the data is converted
                 into whatever format the validation uses (by default Django's
                 Forms) If not, the data is returned unchanged.
        :raises: HttpStatusCodeError if data is not valid
        """

        validator = self._get_input_validator(request)
        if isinstance(data, (list, tuple)):
            return map(validator.validate, data)
        else:
            return validator.validate(data)

    def _validate_output_data(
        self, original_res, serialized_res, formatted_res, request):
        """ Validate the response data.

        :param response: ``HttpResponse``
        :param data: payload data. This implementation assumes
                     dict or list of dicts.
        :raises: `HttpStatusCodeError` if data is not valid
        """

        validator = self.representation

        # when not to validate...
        if not validator:
            return

        try:
            if isinstance(serialized_res, (list, tuple)):
                map(validator.validate, serialized_res)
            else:
                validator.validate(serialized_res)
        except ValidationError, exc:
            self._output_validation_failed(exc, serialized_res, request)

    def _input_validation_failed(self, error, data, request):
        """ Always raises HttpStatusCodeError.

        Override to raise different status code when request data
        doesn't pass validation.

        todo: should format the content using the datamapper
        """

        raise errors.BadRequest(str(error))

    def _output_validation_failed(self, error, data, request):
        """ Always raises HttpStatusCodeError.

        Override to raise different status code when response data
        doesn't pass validation.
        """

        raise errors.InternalServerError(str(error))

    def _create_object(self, data, request):
        """ Create a python object from the given data.

        This will use ``self.factory`` object's ``create()`` function to
        create the data.

        If no factory is defined, this will simply return the same data
        that was given.
        """

        if request.method.upper() == 'POST' and self.post_factory:
            fac_func = self.post_factory.create
        else:
            fac_func = self.factory.create

        if isinstance(data, (list, tuple)):
            return map(fac_func, data)
        else:
            return fac_func(data)

    def _serialize_object(self, response_data, request):
        """ Create a python datatype from the given python object.

        This will use ``self.factory`` object's ``serialize()`` function
        to convert the object into dictionary.

        If no factory is defined, this will simply return the same data
        that was given.

        :param response_data: data returned by the resource
        """

        if not self.factory:
            return response_data
        if isinstance(response_data, (list, tuple)):
            return map(
                lambda item: self.factory.serialize(item, request),
                response_data)
        else:
            return self.factory.serialize(response_data, request)

    def _get_unknown_error_response(self, request, exc):
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
            if exc.has_code(codes.INTERNAL_SERVER_ERROR):
                logging.getLogger('devil').error('devil caught http error: ' + str(exc), exc_info=True)
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
            created and initialized with `AnonymousUser`.
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
