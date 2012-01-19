#  -*- coding: utf-8 -*-
# tests.py ---
#
# Created: Fri Dec 30 23:38:50 2011 (+0200)
# Author: Janne Kuuskeri
#


import json, base64, logging
from decimal import Decimal
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import Client
from drest import datamapper
from drest import errors, http
from drest.perm import management as syncdb
import urls as testurls


# mute the log (enable when debugging)
log = logging.getLogger('drest')
log.setLevel(logging.FATAL)


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
            {'content_type_id': 1, 'codename': 'resource_mypermresource_post'},
            {'content_type_id': 1, 'codename': 'resource_mypermresource_get'},
            {'content_type_id': 1, 'codename': 'resource_mypermresource_put'},
            {'content_type_id': 1, 'codename': 'resource_mypermresource_delete'},
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
            # if test['method'] in ('put', 'post'):
            #     response = getattr(client, test['method'])(
            #         '/simple/perm',
            #         '{"a": 1}',
            #         'application/json;charset=utf-8')
            # else:
            response = getattr(client, test['method'])('/simple/perm')
            self.assertEquals(
                response.status_code,
                test['status'],
                '%d != %d: %s %s: %s' % (response.status_code, test['status'], test['user'], test['method'], response.content))


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
            self.assertEquals(
                response.status_code,
                result,
                '%d != %d: %s/%s' % (response.status_code, result, username, password))


class HttpParseTest(TestCase):
    """ Test parsing using test client """

    def test_put_contenttype(self):
        client = Client()
        response = client.put(
            '/simple/mapper/dict/',
            '{"a": 1.99}',
            'application/json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEquals(response.content, '')
        self.assertEquals(testurls.dictresource.mydata, {'a': 1.99})

    def test_post_empty_data(self):
        client = Client()
        response = client.put(
            '/simple/mapper/dict/',
            '',
            'application/json')
        self.assertEquals(response.status_code, 200)

    def test_my_mapper(self):
        client = Client()
        response = client.put(
            '/simple/mapper/reverse',
            'reppam ,olleh',
            'text/plain')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEquals(testurls.mapperresource.last_data, 'hello, mapper')
        self.assertEquals(response.content, '')


class HttpFormatTest(TestCase):
    """ Test formatting using test client """

    def test_qs(self):
        client = Client()
        response = client.get('/simple/mapper/dict/?format=json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(json.loads(response.content), {"a": 3.99, "b": 3.99})

    def test_extension(self):
        client = Client()
        response = client.get('/simple/mapper/dict/hiihoo.json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(json.loads(response.content), {"a": 3.99, "b": 3.99})

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

    def test_none_response(self):
        client = Client()
        response = client.get('/simple/mapper/none?format=json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '')

    def test_json_from_response(self):
        client = Client()
        response = client.get('/simple/mapper/resp/?format=json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(json.loads(response.content), {"jedi": "luke"})

    def test_my_mapper(self):
        client = Client()
        response = client.get('/simple/mapper/reverse')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEquals(response.content, 'reppam ,olleh')

    def test_scandic_ascii(self):
        client = Client()
        resp = client.get('/simple/mapper/scandic')
        self.assertEquals(resp.status_code, 500)

    def test_scandic_ascii_json(self):
        client = Client()
        resp = client.get('/simple/mapper/scandic/json')
        self.assertEquals(resp.status_code, 500)


class JsonDecimalMapperTests(TestCase):
    """ Test the JsonDecimalMapper """

    def setUp(self):
        from drest.datamapper import JsonMapper, JsonDecimalMapper, manager
        manager.register_mapper(JsonDecimalMapper(), 'application/json', 'json')

    def tearDown(self):
        from drest.datamapper import JsonMapper, JsonDecimalMapper, manager
        manager.register_mapper(JsonMapper(), 'application/json', 'json')

    def test_parse(self):
        client = Client()
        resp = client.get('/simple/mapper/decimal?format=json')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content, '{\n    "a": 3.99,\n    "b": 3.99\n}')

    def test_format(self):
        client = Client()
        resp = client.put(
            '/simple/mapper/decimal',
            '{"a": 3.99, "b": 3.99}',
            'application/json')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(testurls.decimalresource.mydata, {
            'a': Decimal('3.99'),
            'b': Decimal('3.99'),
            })


class MapperFormatTest(TestCase):
    """ Test formatting directly """

    def test_unknown_by_content_type(self):
        """ Test that request content-type doesn't affect anything. """
        request = FakeRequest('/hiihoo.json', 'hiihootype')
        response = datamapper.format(request, {'a': 1})
        self.assertEquals(json.loads(response.content), {'a': 1})
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

    def test_none_data_default(self):
        request = FakeRequest('/hiihoo')
        response = datamapper.format(request, None)
        self.assertEquals(response.content, '')
        self.assertEquals(response.status_code, 0)
        self.assertEquals(response['Content-Type'], 'text/plain; charset=utf-8')

    def test_none_data_json(self):
        request = FakeRequest('/hiihoo', format='json')
        response = datamapper.format(request, None)
        self.assertEquals(response.content, '')
        self.assertEquals(response.status_code, 0)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')

    def test_my_default_formatter(self):
        class MyDataMapper(datamapper.DataMapper):
            content_type = 'text/jedi'
            def _format_data(self, data, charset):
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
        self.assertEquals(json.loads(response.content), {"a": 1})
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.status_code, 0)

    def test_no_data(self):
        request = FakeRequest('/hiihoo.json')
        self.assertEquals((datamapper.format(request, None)).content, '')
        request = FakeRequest('/hiihoo.json', '')
        self.assertEquals((datamapper.format(request, '')).content, '')
        request = FakeRequest('/hiihoo.json', '{}')
        self.assertEquals('{}', (datamapper.format(request, {})).content)
        request = FakeRequest('/hiihoo.json', '[]')
        self.assertEquals('[]', (datamapper.format(request, [])).content)


class MapperParseTest(TestCase):
    """ Test parsing directly """

    def test_unknown_by_content_type(self):
        request = FakeRequest('/hiihoo.json', 'hiihoo', 'hiihootype')
        self.assertRaises(errors.NotAcceptable, datamapper.parse, 'hiihoo', request)

    def test_unknown_by_extension(self):
        request = FakeRequest('/hiihoo.yaml', 'hiihoo')
        self.assertRaises(errors.NotAcceptable, datamapper.parse, 'hiihoo', request)

    def test_unknown_by_qs(self):
        request = FakeRequest('/hiihoo', 'hiihoo', format='yaml')
        self.assertRaises(errors.NotAcceptable, datamapper.parse, 'hiihoo', request)

    def test_default_parser(self):
        request = FakeRequest('/hiihoo', '{"a": 1}')
        self.assertEquals('{"a": 1}', datamapper.parse('{"a": 1}', request))

    def test_json_by_content_type(self):
        request = FakeRequest('/hiihoo', '{"a": 1}', 'application/json')
        self.assertEquals({'a': 1}, datamapper.parse('{"a": 1}', request))
        request = FakeRequest('/hiihoo.yaml', '{"a": 1}', 'application/json')
        self.assertEquals({'a': 1}, datamapper.parse('{"a": 1}', request))
        request = FakeRequest('/hiihoo.yaml', '{"a": 1}', 'application/json', format='yaml')
        self.assertEquals({'a': 1}, datamapper.parse('{"a": 1}', request))

    def test_json_by_qs(self):
        request = FakeRequest('/hiihoo', '{"a": 1}', format='json')
        self.assertEquals({'a': 1}, datamapper.parse('{"a": 1}', request))
        request = FakeRequest('/hiihoo.yaml', '{"a": 1}', format='json')
        self.assertEquals({'a': 1}, datamapper.parse('{"a": 1}', request))

    def test_json_by_extension(self):
        request = FakeRequest('/hiihoo.json', '{"a": 3, "b": 4}')
        self.assertEquals(datamapper.parse('{"a": 3, "b": 4}', request), {'a': 3, 'b': 4})

    def test_bad_data(self):
        request = FakeRequest('/hiihoo.json', 'hiihoo')
        self.assertRaises(errors.BadRequest, datamapper.parse, 'hiihoo', request)

    def test_no_data(self):
        request = FakeRequest('/hiihoo.json')
        self.assertRaises(TypeError, datamapper.parse, request)
        request = FakeRequest('/hiihoo.json', '')
        self.assertRaises(errors.BadRequest, datamapper.parse, 'hiihoo', request)
        request = FakeRequest('/hiihoo.json', '{}')
        self.assertEquals({}, datamapper.parse('{}', request))
        request = FakeRequest('/hiihoo.json', '[]')
        self.assertEquals([], datamapper.parse('[]', request))


class MapperTest(TestCase):

    class MyDataMapper(datamapper.DataMapper):
        charset = 'iso-8859-1'

    class AsciiMapper(datamapper.DataMapper):
        charset = 'ascii'

    class AsciiJsonMapper(datamapper.JsonMapper):
        charset = 'ascii'

    def test_format_my_mapper(self):
        m = self.MyDataMapper()
        resp = m.format('hello')
        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEquals(resp.status_code, 0)
        self.assertEquals(resp['Content-Type'], 'text/plain; charset=iso-8859-1')
        self.assertEquals(resp.content, 'hello')

    def test_format_none(self):
        m = datamapper.DataMapper()
        resp = m.format(None)
        self.assertEquals(resp.content, '')
        self.assertTrue(isinstance (resp.content, str))

    def test_format_scandic_uni(self):
        m = datamapper.DataMapper()
        # give unicode to mapper
        resp = m.format(u'lähtö')
        self.assertEquals(resp.content, 'lähtö')
        self.assertTrue(isinstance (resp.content, str))

    def test_format_scandic_str(self):
        m = datamapper.DataMapper()
        # give str to mapper
        resp = m.format('lähtö')
        self.assertEquals(resp.content, 'lähtö')
        self.assertTrue(isinstance (resp.content, str))

    def test_ascii_mapper_scandic(self):
        m = self.AsciiMapper()
        self.assertRaises(UnicodeEncodeError, m.format, u'lähtö')
        self.assertRaises(errors.BadRequest, m.parse, 'lähtö')

    def test_parse_scandic(self):
        m = datamapper.DataMapper()
        result = m.parse('lähtö')
        self.assertEquals(result, u'lähtö')
        self.assertTrue(isinstance (result, unicode))

    def test_parse_scandic_json(self):
        m = datamapper.JsonMapper()
        result = m.parse('{"key": "lähtö"}', 'utf-8')
        self.assertTrue(isinstance (result['key'], unicode))

    def test_format_scandic_json(self):
        m = datamapper.JsonMapper()
        data = {'key': 'lähtö'}
        resp = m.format(data)
        self.assertEquals(resp['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(resp.content, '{\n    "key": "lähtö"\n}')

    def test_format_scandic_ascii_json(self):
        m = self.AsciiJsonMapper()
        data = {'key': 'lähtö'}
        self.assertRaises(UnicodeDecodeError, m.format, data)
        data = {u'key': u'lähtö'}
        resp = m.format(data)
        self.assertEquals(resp['Content-Type'], 'application/json; charset=ascii')
        self.assertEquals(resp.content, '{\n    "key": "lähtö"\n}')


class ValidationTest(TestCase):

    def test_parse_validation_pass(self):
        client = Client()
        response = client.put(
            '/simple/valid?format=json',
            '{"name": "Luke"}',
            'application/json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '')

    def test_parse_validation_pass_extra(self):
        client = Client()
        response = client.put(
            '/simple/valid?format=json',
            '{"name": "Luke", "extra": "data"}',
            'application/json')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEquals(response.content, '')

    def test_parse_validation_fail(self):
        client = Client()
        response = client.put(
            '/simple/valid?format=json',
            '{"name": "Luke Skywalker"}',
            'application/json')
        self.assertEquals(response.status_code, 400)

    def test_format_validation_pass(self):
        client = Client()
        response = client.get('/simple/valid?format=json&status=good')
        self.assertEquals(response.status_code, 200)

    def test_format_validation_list_pass(self):
        client = Client()
        response = client.get('/simple/valid?format=json&status=goodlist')
        self.assertEquals(response.status_code, 200)

    def test_format_validation_list_fail(self):
        client = Client()
        response = client.get('/simple/valid?format=json&status=badlist')
        self.assertEquals(response.status_code, 500)

    def test_format_validation_fail1(self):
        client = Client()
        response = client.get('/simple/valid?format=json&a=b')
        self.assertEquals(response.status_code, 500)

    def test_format_validation_fail2(self):
        client = Client()
        response = client.get('/simple/valid?format=json&status=none')
        self.assertEquals(response.status_code, 200)


class DefaultMapperTest(TestCase):

    def test_default_txt(self):
        client = Client()
        response = client.get('/simple/mapper/default/txt')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '{\n    "key": "löyhkä"\n}')

    def test_default_obj(self):
        client = Client()
        response = client.get('/simple/mapper/default/obj')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '{\n    "key": "löyhkä"\n}')


#
# tests.py ends here
