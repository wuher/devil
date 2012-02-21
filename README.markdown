# Simple REST frameword for Django

Devil aims to be simple to use REST framework for Django. Devil is
influenced by [piston][1].

## Key Characteristics

  - `Resource` is the key concept, everything builds around it.
  - Builtin content negotiation (parsers / formatters).
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
      model and representation
  - Ability to define representation using Django's forms
    - Automatic validation of incoming/outgoing data
    - Automatic documentation generation (_Not implemented yet_)


## Installation

    pip install devil

Source code can be found from [GitGub][7]


## Example

myresources.py:

    from devil.resource import Resource

    class MyTestResource(Resource):
        def get(self, request):
            return {'jedi': 'luke'}

urls.py:

    from django.conf.urls.defaults import patterns, url
    from devil.resource import Resource
    import myresources

    mytestresource = myresources.MyTestResource()
    urlpatterns = patterns('',
        url(r'^test', mytestresource),
    )

curl:

    curl http://localhost:8000/test&format=json

    > GET /contact/?format=json HTTP/1.1
    > User-Agent: curl/7.21.4 (universal-apple-darwin11.0) libcurl/7.21.4
    > Host: localhost:8000
    > Accept: */*
    >
    < HTTP/1.0 200 OK
    < Date: Tue, 14 Feb 2012 09:35:02 GMT
    < Server: WSGIServer/0.1 Python/2.7.1
    < Content-Type: application/json; charset=utf-8
    <
        {
            "jedi": "luke"
        }


## Content Negotiation

Devil uses the terms `parser` and `formatter` for data decoding and encoding
respectively. They are collectively referred to as data `mappers`. By default,
devil tries to parse all data that comes in with `PUT` and `POST` requests.
Similarly, devil automatically formats all outgoing data when it is present.
Appropriate mapper can be defined in one of the following places (note that this list is not sorted by precedence):

  - In the URL:
    - either with `?format=json` 
    - or with `.json` suffix
  - HTTP [Accept][2] header
  - HTTP [Content-Type][3] header (meaningful only for `PUT`s and `POST`s)
  - A resource may define its own mapper which will always be used
     - define `mapper` in your derived `Resource` class (see [examples][4])
  - A resource may define a default mapper that will be used if the client
    specifies no content type
     - define `default_mapper` in your derived `Resource` class (see [examples][4])
  - Application may define one system wide default mapper by registering a 
    mapper with content type `*/*`

If the client specifies a content type that is not supported, devil responds
with `406 Not Acceptable`. Out of the box, devil supports `plain/text`,
`application/json` and `text/xml`. You can register more mappers for your
application of course. It should be noted that the built-in XML mapper has
some restrictions (see the [docstring][5]).

Following picture formally defines how a correct formatter is chosen for
encoding the outgoing data:

![Selecting a formatter](https://github.com/wuher/devil/raw/master/doc/select-formatter.pdf "Selecting a formatter")


Likewise, the next picture defines how a correct parser is chosen for the
incoming (via `PUT` or `POST`) data:

![Selecting a parser](https://github.com/wuher/devil/raw/master/doc/select-parser.pdf "Selecting a parser")

See the [docstrings][6] in the `DataMapper` class and the [example
resources][4] in tests for instructions on how to implement your own mappers.


## License


(The MIT License)

Copyright (c) 2012 Janne Kuuskeri

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


[1]:https://bitbucket.org/jespern/django-piston/wiki/Home
[2]:http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.1
[3]:http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.17
[4]:https://github.com/wuher/devil/blob/master/test/deviltest/simple/resources.py
[5]:https://github.com/wuher/devil/blob/master/devil/mappers/xmlmapper.py
[6]:https://github.com/wuher/devil/blob/master/devil/datamapper.py
[7]:https://github.com/wuher/devil
