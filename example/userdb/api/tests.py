#  -*- coding: utf-8 -*-
#  tests.py ---
#  created: 2012-03-14 13:17:42
#


from django.test import TestCase
from django.test.client import Client
import json


class CRUDTest(TestCase):

    fixtures = [
        'user_fixture.json',
    ]

    def test_get_all(self):
        client = Client()
        response = client.get('/user/')
        self.assertEquals(200, response.status_code)
        data = json.loads(response.content)
        self.assertEquals(2, len(data))

    def test_get_one(self):
        client = Client()
        response = client.get('/user/1')
        self.assertEquals(200, response.status_code)
        data = json.loads(response.content)
        self.assertEquals(
            {
                'name': 'Luke Skywalker',
                'age': 33,
            },
            data)

    def test_get_missing(self):
        client = Client()
        response = client.get('/user/9')
        self.assertEquals(404, response.status_code)

    def test_post(self):
        client = Client()
        response = client.post(
            '/user/',
            '{"name": "Yoda", "age": 879}',
            'application/json')
        self.assertEquals(201, response.status_code)
        self.assertTrue(response['location'].endswith('/user/3'))
        response = client.get('/user/3')
        self.assertEquals(200, response.status_code)
        data = json.loads(response.content)
        self.assertEquals(
            {
                'name': 'Yoda',
                'age': 879,
            },
            data)

    def test_post_to_user(self):
        client = Client()
        response = client.post(
            '/user/4',
            '{"name": "Yoda", "age": 879}',
            'application/json')
        self.assertEquals(405, response.status_code)

    def test_post_bad_data(self):
        client = Client()
        response = client.post(
            '/user/',
            '{"game": "Yoda", "age": 879}',
            'application/json')
        self.assertEquals(400, response.status_code)

    def test_put(self):
        client = Client()
        response = client.put(
            '/user/2',
            '{"name": "Darth Maul", "age": 33}',
            'application/json')
        self.assertEquals(200, response.status_code)
        response = client.get('/user/2')
        data = json.loads(response.content)
        self.assertEquals(
            {
                'name': 'Darth Maul',
                'age': 33,
            },
            data)

    def test_put_top_level(self):
        client = Client()
        response = client.put(
            '/user/',
            '{"name": "Darth Maul", "age": 33}',
            'application/json')
        self.assertEquals(405, response.status_code)

    def test_put_bad_data(self):
        client = Client()
        response = client.put(
            '/user/2',
            '{"game": "Darth Maul", "age": 33}',
            'application/json')
        self.assertEquals(400, response.status_code)

    def test_delete(self):
        client = Client()
        response = client.delete('/user/2')
        self.assertEquals(200, response.status_code)

    def test_delete_missing(self):
        client = Client()
        response = client.delete('/user/9')
        self.assertEquals(200, response.status_code)

    def test_delete_top_level(self):
        client = Client()
        response = client.delete('/user/')
        self.assertEquals(405, response.status_code)

#
#  tests.py ends here
