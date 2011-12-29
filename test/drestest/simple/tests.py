"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""


import json, base64
from django.test import TestCase
from django.test.client import Client
from drest import datamapper
from drest import errors, http
from drest.perm import management as syncdb
import urls as testurls


class FakeRequest(object):
    """ Fake request to test mappers (parsing / formatting). """

    def __init__(self, path, content=None, content_type=None, **kw):
        self.GET = kw
        self.raw_post_data = content
        self.path = path
        self.META = {}
        if content_type:
            self.META['CONTENT_TYPE'] = content_type


class DrestClient(Client):
    """ Adds HTTP Basic authentication to django's test client. """

    def __init__(self, username=None, password=None, *args, **kw):
        Client.__init__(self, *args, **kw)
        self._authorization = {}
        if username and password:
            auth = base64.b64encode('%s:%s' % (username, password))
            self._authorization = {
                'HTTP_AUTHORIZATION': 'Basic %s' % (auth,)
                }

    def _get_params(self, **kw):
        params = self._authorization.copy()
        params.update(kw)
        return params

    def get(self, path, data={}, *args, **kw):
        return super(DrestClient, self).get(
            path, data, *args, **(self._get_params(**kw)))

    def post(self, path, data={}, *args, **kw):
        return super(DrestClient, self).post(
            path, data, *args, **(self._get_params(**kw)))

    def put(self, path, data={}, *args, **kw):
        return super(DrestClient, self).put(
            path, data, *args, **(self._get_params(**kw)))

    def delete(self, path, data={}, *args, **kw):
        return super(DrestClient, self).delete(
            path, data, *args, **(self._get_params(**kw)))


class PermSyncDbTest(TestCase):
    """ Tests to verify that syncdb initializes permissions into the database.

    todo: test various settins.ACL_RESOURCES values
    """

    def test_content_type(self):
        from django.contrib.contenttypes.models import ContentType

        conttype = ContentType.objects.get(name='drest')
        self.assertEquals(conttype.name, 'drest')
        self.assertEquals(conttype.app_label, 'drest')
        self.assertEquals(conttype.model, 'drest')

    def test_permissions(self):
        from django.contrib.auth.models import Permission
        perms = dict([(p.codename, p) for p in Permission.objects.filter(content_type__id=1)])
        self.assertEquals(len(perms), 4)

        expected = (
            {'content_type_id': 1, 'codename': 'resource_MyPermResource_post'},
            {'content_type_id': 1, 'codename': 'resource_MyPermResource_get'},
            {'content_type_id': 1, 'codename': 'resource_MyPermResource_put'},
            {'content_type_id': 1, 'codename': 'resource_MyPermResource_delete'},
        )

        for exp in expected:
            self.assertTrue(exp['codename'] in perms)


class PermTest(TestCase):
    """ Test permissions. """

    fixtures = [
        'auth_user.json',
        ]

    def setUp(self):
        """ Initialize permisssions

        jedi gets all permissions and sith gets read-only permsissions
        """

        from django.contrib.auth.models import Permission, User
        perms = Permission.objects.filter(codename__startswith='resource_')
        jedi = User.objects.get(username='jedi')
        sith = User.objects.get(username='sith')
        for perm in perms:
            if perm.codename.endswith('_get'):
                sith.user_permissions.add(perm)
            jedi.user_permissions.add(perm)
        jedi.save()
        sith.save()

    def test_permissions(self):
        tests = (
            {'user': 'yoda', 'method': 'get', 'status': 200},
            {'user': 'yoda', 'method': 'put', 'status': 200},
            {'user': 'yoda', 'method': 'post', 'status': 405},
            {'user': 'yoda', 'method': 'delete', 'status': 200},

            {'user': 'jedi', 'method': 'get', 'status': 200},
            {'user': 'jedi', 'method': 'put', 'status': 200},
            {'user': 'jedi', 'method': 'post', 'status': 405},
            {'user': 'jedi', 'method': 'delete', 'status': 200},

            {'user': 'sith', 'method': 'get', 'status': 200},
            {'user': 'sith', 'method': 'put', 'status': 403},
            # note: we get 403, even though resource doesn't even support POST
            {'user': 'sith', 'method': 'post', 'status': 403},
            {'user': 'sith', 'method': 'delete', 'status': 403},
            )

        for test in tests:
            client = DrestClient(username=test['user'], password=test['user'])
            response = getattr(client, test['method'])('/simple/perm')
            self.assertEquals(response.status_code, test['status'])


class AuthTest(TestCase):
    """ Test authentication. """

    fixtures = [
        'auth_user.json',
        ]

    def test_auth(self):
        tests = (
            (None, None, 401),
            ('john', 'doe', 403),
            ('sith', 'jedi', 403),
            ('jedi', 'jedi', 200),
            ('sith', 'sith', 200),
            )
        for username, password, result in tests:
            client = DrestClient(username=username, password=password)
            response = client.get('/simple/auth')
            self.assertEquals(response.status_code, result)

    def test_anon_auth(self):
        tests = (
            (None, None, 200),
            ('john', 'doe', 403),
            ('sith', 'jedi', 403),
            ('jedi', 'jedi', 200),
            ('sith', 'sith', 200),
            )
        for username, password, result in tests:
            client = DrestClient(username=username, password=password)
            response = client.get('/simple/auth/anon')
            self.assertEquals(response.status_code, result)


class HttpParseTest(TestCase):
    """ Test parsing using test client """

    def test_put_contenttype(self):
        client = Client()
        response = client.put(
            '/simple/mapper/dict/',
            '{"a": 1}',
            'application/json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEquals(response.content, '')
        self.assertEquals(testurls.dictresource.mydata, {'a': 1})

    def test_post_empty_data(self):
        client = Client()
        response = client.put(
            '/simple/mapper/dict/',
            '',
            'application/json')
        self.assertEquals(response.status_code, 400)


class HttpFormatTest(TestCase):
    """ Test formatting using test client """

    def test_qs(self):
        client = Client()
        response = client.get('/simple/mapper/dict/?format=json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '{"a": 3, "b": 4}')

    def test_extension(self):
        client = Client()
        response = client.get('/simple/mapper/dict/hiihoo.json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '{"a": 3, "b": 4}')

    def test_default(self):
        client = Client()
        response = client.get('/simple/mapper/text/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEquals(response.content, 'hello text')

    def test_json_from_txt(self):
        client = Client()
        response = client.get('/simple/mapper/text/?format=json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '"hello text"')

    def test_json_from_response(self):
        client = Client()
        response = client.get('/simple/mapper/resp/?format=json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '{"jedi": "luke"}')


class MapperFormatTest(TestCase):
    """ Test formatting directly """

    def test_unknown_by_content_type(self):
        """ Test that request content-type doesn't affect anything. """
        request = FakeRequest('/hiihoo.json', 'hiihootype')
        response = datamapper.format(request, {'a': 1})
        self.assertEquals(response.content, '{"a": 1}')
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')

    def test_unknown_by_extension(self):
        request = FakeRequest('/hiihoo.yaml')
        self.assertRaises(errors.NotAcceptable, datamapper.format, request, {'a': 1})

    def test_unknown_by_qs(self):
        request = FakeRequest('/hiihoo', format='yaml')
        self.assertRaises(errors.NotAcceptable, datamapper.format, request, {'a': 1})

    def test_default_formatter(self):
        request = FakeRequest('/hiihoo')
        response = datamapper.format(request, 'Hello, world!')
        self.assertEquals(response.content, 'Hello, world!')
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')

    def test_my_default_formatter(self):
        class MyDataMapper(datamapper.DataMapper):
            content_type = 'text/jedi'
            def _format_data(self, data):
                return 'this is my data, i have nothing else'

        # install my own default mapper
        datamapper.manager.set_default_mapper(MyDataMapper())
        request = FakeRequest('/hiihoo')
        response = datamapper.format(request, 'Hello, world!')
        self.assertEquals(response.content, 'this is my data, i have nothing else')
        self.assertEquals(response['Content-Type'], 'text/jedi; charset=utf-8')

        # put the original default mapper back
        datamapper.manager.set_default_mapper(None)
        request = FakeRequest('/hiihoo')
        response = datamapper.format(request, 'Hello, world!')
        self.assertEquals(response.content, 'Hello, world!')
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')

    def test_response_to_json(self):
        request = FakeRequest('/', format='json')
        response = datamapper.format(request, http.Response(0, {'a': 1}))
        self.assertEquals(response.content, '{"a": 1}')
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.status_code, 0)


class MapperParseTest(TestCase):
    """ Test parsing directly """

    def test_unknown_by_content_type(self):
        request = FakeRequest('/hiihoo.json', 'hiihoo', 'hiihootype')
        self.assertRaises(errors.NotAcceptable, datamapper.parse, request)

    def test_unknown_by_extension(self):
        request = FakeRequest('/hiihoo.yaml', 'hiihoo')
        self.assertRaises(errors.NotAcceptable, datamapper.parse, request)

    def test_unknown_by_qs(self):
        request = FakeRequest('/hiihoo', 'hiihoo', format='yaml')
        self.assertRaises(errors.NotAcceptable, datamapper.parse, request)

    def test_default_parser(self):
        request = FakeRequest('/hiihoo', '{"a": 1}')
        self.assertEquals('{"a": 1}', datamapper.parse(request))

    def test_json_by_content_type(self):
        request = FakeRequest('/hiihoo', '{"a": 1}', 'application/json')
        self.assertEquals({'a': 1}, datamapper.parse(request))
        request = FakeRequest('/hiihoo.yaml', '{"a": 1}', 'application/json')
        self.assertEquals({'a': 1}, datamapper.parse(request))
        request = FakeRequest('/hiihoo.yaml', '{"a": 1}', 'application/json', format='yaml')
        self.assertEquals({'a': 1}, datamapper.parse(request))

    def test_json_by_qs(self):
        request = FakeRequest('/hiihoo', '{"a": 1}', format='json')
        self.assertEquals({'a': 1}, datamapper.parse(request))
        request = FakeRequest('/hiihoo.yaml', '{"a": 1}', format='json')
        self.assertEquals({'a': 1}, datamapper.parse(request))

    def test_json_by_extension(self):
        request = FakeRequest('/hiihoo.json', '{"a": 3, "b": 4}')
        self.assertEquals(datamapper.parse(request), {'a': 3, 'b': 4})

    def test_bad_data(self):
        request = FakeRequest('/hiihoo.json', 'hiihoo')
        self.assertRaises(errors.BadRequest, datamapper.parse, request)

    def test_no_data(self):
        request = FakeRequest('/hiihoo.json')
        self.assertRaises(TypeError, datamapper.parse, request)
        request = FakeRequest('/hiihoo.json', '')
        self.assertRaises(errors.BadRequest, datamapper.parse, request)
        request = FakeRequest('/hiihoo.json', '{}')
        self.assertEquals({}, datamapper.parse(request))
        request = FakeRequest('/hiihoo.json', '[]')
        self.assertEquals([], datamapper.parse(request))

