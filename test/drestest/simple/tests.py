"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""


import json
from django.test import TestCase
from django.test.client import Client
from drest import parsers
from drest import errors


class FakeRequest(object):
    def __init__(self, content, path, content_type=None, **kw):
        self.GET = kw
        self.raw_post_data = content
        self.path = path
        self.META = {}
        if content_type:
            self.META['CONTENT_TYPE'] = content_type


class SimpleTest(TestCase):
    def test_parsing(self):
        client = Client()
        response = client.get('/simple/test/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "{'a': 3, 'b': 4}")


class ParseTest(TestCase):
    def test_unknown_by_content_type(self):
        request = FakeRequest('hiihoo', '/hiihoo.json', 'hiihoo')
        self.assertRaises(errors.BadRequest, parsers.parse, request)

    def test_unknown_by_extension(self):
        request = FakeRequest('hiihoo', '/hiihoo.yaml')
        self.assertRaises(errors.BadRequest, parsers.parse, request)

    def test_unknown_by_qs(self):
        request = FakeRequest('hiihoo', '/hiihoo', format='yaml')
        self.assertRaises(errors.BadRequest, parsers.parse, request)

    def test_default_parser(self):
        request = FakeRequest('{"a": 1}', '/hiihoo')
        self.assertEquals('{"a": 1}', parsers.parse(request))

    def test_json_by_content_type(self):
        request = FakeRequest('{"a": 1}', '/hiihoo', 'application/json')
        self.assertEquals({'a': 1}, parsers.parse(request))
        request = FakeRequest('{"a": 1}', '/hiihoo.yaml', 'application/json')
        self.assertEquals({'a': 1}, parsers.parse(request))
        request = FakeRequest('{"a": 1}', '/hiihoo.yaml', 'application/json', format='yaml')
        self.assertEquals({'a': 1}, parsers.parse(request))

    def test_json_by_qs(self):
        request = FakeRequest('{"a": 1}', '/hiihoo', format='json')
        self.assertEquals({'a': 1}, parsers.parse(request))
        request = FakeRequest('{"a": 1}', '/hiihoo.yaml', format='json')
        self.assertEquals({'a': 1}, parsers.parse(request))

    def test_json_by_extension(self):
        request = FakeRequest('{"a": 3, "b": 4}', '/hiihoo.json')
        self.assertEquals(parsers.parse(request), {'a': 3, 'b': 4})

    def test_bad_data(self):
        request = FakeRequest('hiihoo', '/hiihoo.json')
        self.assertRaises(errors.BadRequest, parsers.parse, request)

    def test_no_data(self):
        request = FakeRequest(None, '/hiihoo.json')
        self.assertRaises(errors.BadRequest, parsers.parse, request)
        request = FakeRequest('', '/hiihoo.json')
        self.assertRaises(errors.BadRequest, parsers.parse, request)
        request = FakeRequest('{}', '/hiihoo.json')
        self.assertEquals({}, parsers.parse(request))
        request = FakeRequest('[]', '/hiihoo.json')
        self.assertEquals([], parsers.parse(request))

