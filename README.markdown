**THIS IS A WORK IN PROGRESS**

Simple REST frameword for Django
================================

dRest aims to be simple to use REST framework for Django. dRest is
influenced by [piston][1].


Key Characteristics
-------------------

  - `Resource` is the key concept, everything builds around it.
  - Automatic content negotiation (parsers / formatters).
  - Gets out of your way
    - You can use additional features but you don't need to.
    - Everything is optional and works with default values.
    - Simple to get started.
  - Flexible access control based on Django's users, groups and
    permissions.
    - Ability to assign CRUD operations per resource for
      each user (or group)
    - dRest will auto-generate necessary permissions into the DB
    - You can use Django's admin interface to assign permissions to users and groups
    - After this dRest automatically picks up `request.user` and performs authorization
  - Intentionally doesn't give you CRUD for free as piston does
    - We can add this option later if it's concidered useful, but:
    - This rarely works for legacy systems anyway
    - For anything bigger, it's usually a good idea to decouple
      model and presentation
  - Ability to define representation using Django's forms
    - Automatic validation of incoming/outgoing data
    - Automatic documentation generation


Example
-------

myresources.py:

    from drest.resource import Resource
    from drest.http import Response


    class MyTestResource(Resource):
        def get(self, request, *args, **kw):
            return {'jedi': 'luke'}

urls.py:

    from django.conf.urls.defaults import patterns, include, url
    from drest.resource import Resource
    import myresources

    mytestresource = myresources.MyTestResource()
    urlpatterns = patterns('',
        url(r'^test', mytestresource),
    )


[1]:https://bitbucket.org/jespern/django-piston/wiki/Home

