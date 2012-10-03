#  -*- coding: utf-8 -*-
#  tests.py ---
#  created: 2012-09-20 10:09:38
#
#  author: Janne Kuuskeri
#


from django.core.exceptions import ValidationError
from django import forms as django_fields
from django.test import TestCase
from devil.fields import Factory, NestedField, ListField, Representation, \
    EnumField


class Foo(object):
    """ Generic class to be used in tests. """
    pass


class ReverseCharField(django_fields.CharField):
    """ Field to be used in tests.

    This is a char field that reverses itself upon
    cleaning/serialization.
    """

    def to_python(self, value):
        return value[::-1] if value else value

    def from_python(self, value):
        return value[::-1] if value else value


class SubMeaningOfLifeField(NestedField):
    """ For NestedFieldTests """
    meaning = django_fields.CharField(max_length=5)


class MeaningOfLifeField(NestedField):
    """ For NestedFieldTests """
    meaning = django_fields.CharField(max_length=45)
    submeaning = SubMeaningOfLifeField()


class NestedFieldTests(TestCase):
    """ Test NestedField field """

    class Life(object):
        pass

    class LifeRepresentation(Representation):
        id = django_fields.IntegerField()
        lifetype = MeaningOfLifeField()

    def __init__(self, *args, **kw):
        super(NestedFieldTests, self).__init__(*args, **kw)
        self.factory = Factory()
        self.factory.spec = self.LifeRepresentation()
        self.factory.klass = self.Life
        self.factory.property_name_map =\
            self.factory._create_mappings(self.factory.spec)

    def setUp(self):
        self.data = {
            'id': 3,
            'lifetype': {
                'meaning': 'always look at the bright side of the life',
                'submeaning': {
                    'meaning': 'that'
                }
            },
        }

    def test_life(self):
        life = self.factory.create(self.data)
        self.assertEquals(life.id, 3)
        self.assertTrue(life.lifetype.meaning.startswith('always'))
        self.assertEquals(life.lifetype.submeaning.meaning, 'that')
        self.LifeRepresentation().validate(self.data)

    def test_validate_meaning_fails(self):
        self.assertRaises(ValidationError, MeaningOfLifeField().validate, self.data)
        self.data['lifetype']['meaning'] = 'always look at the bright side of the leggings'
        self.assertRaises(ValidationError, self.LifeRepresentation().validate, self.data)

    def test_validate_submeaning_fails(self):
        self.data['lifetype']['submeaning']['meaning'] = 'this is true'
        self.assertRaises(ValidationError, self.LifeRepresentation().validate, self.data)


class ListFieldTests(TestCase):
    """ Test ListField

    Test validation, creation and serialization.
    """

    class MyTestRepresentation(Representation):
        """ Representation to be used in tests """

        rev = ListField(ReverseCharField())
        mylist = ListField(django_fields.CharField(max_length=5))
        myoptlist = ListField(django_fields.CharField(max_length=5), required=False)

    def __init__(self, *args, **kw):
        super(ListFieldTests, self).__init__(*args, **kw)
        self.factory = Factory()
        self.factory.spec = ListFieldTests.MyTestRepresentation()
        self.factory.klass = Foo
        self.factory.property_name_map =\
            self.factory._create_mappings(self.factory.spec)

    def test_validation(self):
        lspec = ListFieldTests.MyTestRepresentation()
        lspec.validate({'rev': ['one'], 'mylist': ['jedi', 'luke', 'shmi']})
        self.assertRaises(ValidationError,
            lspec.validate, {'rev': ['one'], 'mylist': ['jedi', 'luke', 'skywalker']})
        self.assertRaises(ValidationError,
            lspec.validate, {
                'rev': ['one'],
                'mylist': ['jedi'],
                'myoptlist': ['quigon']})

    def test_creation(self):
        foo = self.factory.create({'rev': ['one', 'two'], 'mylist': ['s']})
        self.assertEquals(foo.rev, ['eno', 'owt'])
        self.assertEquals(foo.mylist, ['s'])
        self.assertEquals(foo.myoptlist, None)

    def test_serialization(self):
        foo = Foo()
        foo.rev = ['one', 'two']
        foo.mylist = ['one']
        foo.myoptlist = None
        fdict = self.factory.serialize(foo)
        self.assertEquals(fdict['rev'], ['eno', 'owt'])
        self.assertEquals(fdict['mylist'], ['one'])
        self.assertFalse('myoptlist' in fdict)


class OptionalNested(NestedField):
    """ For FactoryTests """
    davidbrent = django_fields.CharField(required=False)


class TestSpec(Representation):
    id = django_fields.IntegerField()
    name = django_fields.CharField()
    rev1 = ReverseCharField()
    rev2 = ReverseCharField(required=False)
    subs = OptionalNested(required=False)


class FactoryTests(TestCase):
    """ Test factory creation/serialization """

    class TestFactory(Factory):
        """ Test factory that overrides some default behavior. """

        missing = (None, '',)
        klass = Foo
        spec = TestSpec()

        def create_name(self, data, name, spec):
            """ In python, name must always be in upper case. """
            return data[name].upper() if data[name] else data[name]

        def serialize_name(self, value, entity, request):
            """ On the wire, name should always be capitalized. """
            return value.capitalize() if value else value

        def create_rev1(self, data, name, spec):
            """ Override to not reverse the string value. """
            return data[name]

        def serialize_rev1(self, value, entity, request):
            """ Override to not reverse the string value. """
            return value

    def test_create(self):
        """ test factory.create """
        f = self.TestFactory()
        e = f.create({
            'id': 4,
            'name': 'jedi',
            'rev1': 'rev1',
            'rev2': 'rev2',
            'subs': {'davidbrent': 'manager'}})
        self.assertTrue(isinstance(e, Foo))
        self.assertEquals(e.id, 4)
        self.assertEquals(e.name, 'JEDI')  # all upcase
        self.assertEquals(e.rev1, 'rev1')  # this will not be reversed
        self.assertEquals(e.rev2, '2ver')
        self.assertEquals(e.subs.davidbrent, 'manager')

    def test_serialize(self):
        """ test factory.serialize """
        e = Foo()
        e.id = 4
        e.name = 'jedi'
        e.rev1 = 'foo'
        e.rev2 = 'bar'
        f = self.TestFactory()
        d = f.serialize(e)
        self.assertEquals(d['id'], 4)
        self.assertEquals(d['name'], 'Jedi')  # capitalized
        self.assertEquals(d['rev1'], 'foo')  # this will not be reversed
        self.assertEquals(d['rev2'], 'rab')

    def test_serialize_strip_none(self):
        e = Foo()
        e.id = 1
        f = self.TestFactory()
        d = f.serialize(e)
        self.assertEquals(1, d['id'])
        self.assertIsNone(d['name'])
        self.assertIsNone(d['rev1'])
        self.assertFalse('rev2' in d)

    def test_serialize_strip_empty(self):
        e = Foo()
        e.rev2 = ''
        e.id = 1
        f = self.TestFactory()
        d = f.serialize(e)
        self.assertEquals(1, d['id'])
        self.assertIsNone(d['name'])
        self.assertIsNone(d['rev1'])
        self.assertFalse('rev2' in d)

    def test_serialize_dont_strip_empty_list(self):
        e = Foo()
        e.id = 1
        e.rev2 = []
        e.subs = {'davidbrent': None}
        f = self.TestFactory()
        d = f.serialize(e)
        self.assertEquals(1, d['id'])
        self.assertIsNone(d['name'])
        self.assertIsNone(d['rev1'])
        self.assertEquals(d['rev2'], [])
        self.assertFalse('subs' in d)


class EnumFieldTests(TestCase):

    class MySpec(Representation):
        weekday = EnumField(('mon', 'tue', 'wed', 'thu', 'fri'))
        toggle = EnumField([0, 1])

    def test_basic(self):
        spec = self.MySpec()
        spec.validate({'weekday': 'mon', 'toggle': 1})

    def test_failed(self):
        spec = self.MySpec()
        self.assertRaises(ValidationError, spec.validate, {'weekday': 'gon', 'toggle': 1})
        self.assertRaises(ValidationError, spec.validate, {'weekday': 'mon', 'toggle': 2})
        self.assertRaises(ValidationError, spec.validate, {'weekday': ('mon', 'tue'), 'toggle': 1})


#
#  tests.py ends here
