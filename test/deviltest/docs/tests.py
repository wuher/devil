#  -*- coding: utf-8 -*-
#  tests.py ---
#  created: 2012-07-29 23:02:50
#  Author: Janne Kuuskeri
#


from django.test import TestCase
from django.test.client import Client
import json


class DocTests(TestCase):

    def test_get_doc_1(self):
        client = Client()
        response = client.get('/docs/first/3?_doc=false&format=json')
        self.assertEquals(response.status_code, 200)

    def test_get_doc_2(self):
        client = Client()
        response = client.get('/docs/first/3?_doc=true&format=json')
        self.assertEquals(response.status_code, 200)

    def test_get_doc_fail(self):
        client = Client()
        response = client.get('/docs/first/3?doc=true&format=json')
        self.assertEquals(response.status_code, 500)

    def test_get_doc_dict(self):
        client = Client()
        response = client.get('/docs/first/3?_doc&format=json')
        self.assertEquals(response.status_code, 200)
        doc = json.loads(response.content)
        expected = {
            u'resource': u'my/test/resource',
            u'description': u' My test resource\n\n    description of my resource\n    ',
            u'urls': [u'docs/first/(?P<first_id>\\d{1,7})?$'],
            u'methods': {
                u'get': u' hiihoo get\n\n        hiihoo description\n        '
            },
            u'representation': {
                u'age': {
                    u'required': False,
                    u'type': u'IntegerField',
                    u'validators': [],
                },
                u'name': {
                    u'required': False,
                    u'type': u'CharField',
                    u'validators': [{
                        u'MaxLengthValidator': {
                            u'limit_value': 30
                        }
                    }]
                },
                u'weight': {
                    u'required': True,
                    u'type': u'IntegerField',
                    u'validators': []
                }
            }
        }
        self.assertEquals(doc, expected)


#
#  tests.py ends here
