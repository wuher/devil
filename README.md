# Simple REST framework for Django

[Devil][13] aims to be simple to use REST framework for Django. Devil is
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
    - devil will auto-generate necessary permissions into the DB
    - You can use Django's admin interface to assign permissions to users and groups
    - After this devil automatically picks up `request.user` and performs authorization
  - Intentionally doesn't give you CRUD for free as piston does
    - We can add this option later if it's concidered useful, but:
    - This rarely works for legacy systems anyway
    - For anything bigger, it's usually a good idea to decouple
      model and representation
  - Ability to define representation using Django's forms
    - Automatic validation of incoming/outgoing data
    - Automatic documentation generation (_Not implemented yet_)


## Table of Contents

  - [Installation](#installation)
  - [Quick Example](#quick-example)
  - [Step by Step Instructions](#step-by-step-instructions)
  - [URL Dispatching](#url-dispatching)
  - [Method Dispatching](#method-dispatching)
  - [Content Type Negotiation](#content-type-negotiation)
  - [Dealing with Data](#dealing-with-data)
  - [HTTP Responses](#http-responses)
  - [Defining Representations](#defining-representations)
  - [Using Object Factories](#using-object-factories)
  - [Auto-generated Documentation](#auto-generated-documentation)
  - [Configuration](#configuration)
  - [License](#license)


## Installation

    pip install devil

Source code can be found at [GitGub][7]


## Quick Example

resources.py:

```python
from devil.resource import Resource

class MyTestResource(Resource):
    def get(self, request):
        return {'jedi': 'luke'}
```

urls.py:

```python
from django.conf.urls.defaults import patterns, url
from devil.resource import Resource
import resources

mytestresource = resources.MyTestResource()
urlpatterns = patterns('',
    url(r'^test', mytestresource),
)
```

curl:

    curl http://localhost:8000/test?format=json

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

Anoher simple example is available [here][13]


## Step by Step Instructions

    $ pip install devil
    $ django-admin.py startproject phone_book
    $ cd phone_book
    $ python manage.py startapp contacts

contacts/resources.py:

```python
from devil.resource import Resource

class Contact(Resource):
    def get(self, request, *args, **kw):
        return {'name': 'Luke Skywalker'}
```

urls.py:

```python
from django.conf.urls.defaults import patterns, url
from contacts import resources

contacts_resource = resources.Contact()

urlpatterns = patterns('',
    url(r'contact', contacts_resource),
)
```

start the server and in the console say (or you can use a browser):

    $ python manage.py runserver
    $ curl http://localhost:8000/contact?format=json

or if you want to be more HTTP friendly:

    $ curl http://localhost:8000/contact -H 'Accept: application/json'


A more complete example can be found under [examples/userdb][14]. See the README
for instructions on running the example and how to examine the code.


## URL Dispatching

The relationship between URLs and RESTful resources is _one to many_. That is,
one resource may have several URLs mapped to it. Conversely, one URL is always
mapped into a single resource. Devil uses Django's built in [URL
dispatching][8] to define these mappings. If you are familiar with Django's
terms and concepts the resources in Devil become the _views_ of Django.

Say you define your resources in a module called `resources`. Then in your
`urls.py` file you would instantiate and map your resources to URLs, like so:

```python
user_resource = resources.UserResource()

urlpatterns = patterns('',
    url(r'/user', user_resource),
)
```

And to define aliases, you can just add new mappings to the same resource:

```python
urlpatterns = patterns('',
    url(r'/user', user_resource),
    url(r'/jedi', user_resource),
    url(r'/sith', user_resource),
)
```

You can use Django's built-in regexp features like named parameters:

```python
urlpatterns = patterns('',
    url(r'/user(?P<id>\d{1,7})?', user_resource),
)
```

In this case, the `id` property would be available in the resource method:

```python
class UserResource(Resource):
    def get(self, request, id, *args, **kw):
        print id
```

or

```python
class UserResource(Resource):
    def get(self, request, *args, **kw):
        print kw['id']
```


## Method Dispatching

Devil maps the HTTP request methods into functions of the resource directly.
So, if Devil receives an HTTP POST request, it will try and find an instance
method called `post` in the resource and invoke it. If the resource doesn't
define `post` method, Devil will automatically return `405 Mehod Not Allowed`
to the client. The signature for the method for `PUT` and `POST` requests is:

```python
def post(self, data, request):
```

and for others methods:

```python
def get(self, request):
```

so, PUTs and POSTs will have additional `data` attribute that contains the
(possibly parsed) content body of the request. Also, bear in mind that
function parameters may also include named parameters from url mappings.


## Content Type Negotiation

Devil uses the terms `parser` and `formatter` for data decoding and encoding
respectively. They are collectively referred to as data `mappers`. Devil uses
data mappers to parse all data that comes in with `PUT` and `POST` requests
(e.g. JSON, XML or plaintext). Similarly, devil uses data mappers to
automatically format all outgoing data when it is present. The mapper to be used
for a given request can be defined in one of the following places (note that
this list is not sorted by precedence):

  - In the URL:
    - either with `?format=json`
    - or with `.json` suffix
  - HTTP [Accept][2] header. The Accept header supports the full format,
    as in: `Accept: audio/*; q=0.2, audio/basic`
  - HTTP [Content-Type][3] header (meaningful only for `PUT` and `POST`)
  - A resource may define its own mapper which will take precedence over
    anything else
     - define `mapper` in your derived `Resource` class (see [examples][4])
  - A resource may define a default mapper that will be used if the client
    specifies no content type
     - define `default_mapper` in your derived `Resource`
       class (see [examples][4])
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


## Dealing with Data

Once the appropriate data mapper has been chosen, devil can perform
decoding for the incoming data and encoding for the outgoing data. For
example, if a json mapper is chosen your `post` and `get` functions would look
something like this (in terms of data passing):

    $ curl http://localhost:8000/contact -X POST -d '{"name": "Darth Maul", "age": 24}' -H 'Content-Type: application/json'

```python
def post(self, data, request):
    # data is available as a python dict in the data parameter
    print data['name']       # Darth Maul
    print type(data['age'])  # <type 'int'>
```

    $ curl http://localhost:8000/contact/1 -X GET -H 'Accept: application/json'

```python
    def get(self, request):
        # you can return a python dictionary
        return {
            'name': 'Yoda',
            'age': '876',
        }
```

Devil's built-in json and xml mappers will convert to and from python
dictionaries and lists. However, the built-in text (`text/plain`) mapper will
only convert between strings and unicode objects.


## HTTP Responses

A resource (that is, any of its post/get/put/delete methods) may return following
values:

  - dictionary
  - list
  - string
  - `None`
  - Devil's `http.Response`
  - Django's `HttpResponse`

If the resource returns Django's `HttpResponse`, devil doesn't touch the
return value at all but just passes it on to the client. If the return type is
any of the other five, devil tries to encode the data using the appropriate
mapper. Furthermore, devil's `Response` object provides a way for the resource
to include HTTP response code and headers along with the data. Devil will
automatically use response code `200 OK` in cases where the response code
isn't explicitly defined by the resource. Also, devil will automatically add
`Content-Type` HTTP header based on the used data mapper.

Error situations may be handled using exceptions defined in `devil.errors`
package. So whenever there's an error situation and you want to return a certain
response code, you can raise a `HttpStatusCodeError` and devil will
catch it and turn it into appropriate HTTP response object.

```python
from devil import errors
def post(self, data, request):
    if data['age'] > 50:
        # too old
        raise errors.BadRequest("you're too old")
```

In the example, the client would receive `400 BAD REQUEST` with the string
`"you're too old"` in the body whenever the age is above 50.


## Defining Representations

Devil uses Django's [form fields][15] to define representations. By defining
representation for your resource, you gain three advantages: automatic data
validation, possibility to use object factories to automatically create python
objects from your data and the possibility to have [auto-generated documentation
](#auto-generated-documentation) for your resources. The easiest way to define a
representation for your resource is to subclass from [Devil's Representation
class][17] and use fields defined in [Django][15] and [Devil][18] to define all
the properties.

Following example shows a simple representation using Django's form fields:

```python
from django import forms
from devil import Representation

class UserRepresentation(Representation):
    username = forms.CharField(max_length=30)
    joined = forms.DateField(input_formats='%Y-%m-%d')
```

Devil provides couple of handy fields for defining more complex representations,
mainly `NestedField` and `ListField`. These can be used for speficying composite
and collection fields respectively:

```python
from devil.fields import ListField, NestedField, EnumField

class EmailAddress(NestedField):
    email = forms.EmailField()
    type = forms.CharField(required=False)

class UserRepresentation(Representation):
    username = forms.CharField(max_length=30)
    joindate = forms.DateField(input_formats=('%Y-%m-%d',))
    emailAddresses = EmailAddress()
    accountType = EnumField('root', 'novice', 'intermediate')
    tags = ListField(forms.CharField(max_length=20), required=False)
```

The `EmailField` defined here will be reusable in any representation that embeds
email addresses. The `UserRepresentation` on the other hand, is a complete
representation that can be used in a resource to perform automatic data
validation. To see how to put `UserRepresentation` into use, see
[configuration](#representation).


## Using object factories

After a [data mapper](#dealing-with-data) has converted the data into python
dictionary, an object factory may further convert the dictionary into python
object. Against common convention for implementing factories, Devil's
[factory][16] also provides `serialize()` function which is the counter
operation of `create()`.

Factory uses [representation](#defining-representations) object as a
specification when performing object creation and serialization. Normally a
_field_ speficied in the representation knows how to marshal/unmarshal itself
but if not, a subclassed factory may provide `create_foo()` and
`serialize_foo()` functions to provide custom creation/serialization of a field
(`foo` in our example). Following example demonstrates the definition of
`UserFactory`.

```python
from devil import Factory

class User(object):
    pass

class UserFactory(Factory):

    klass = User
    spec = UserRepresentation()

```

An example of manually using `UserFactory`:

```python
testdata = {
    'username': 'jedi',
    'joindate': '2012-01-18',
    'emailAddress': {
        'email': 'jedi@rebillion.net',
        'type': 'work',
    },
    'accountType': 'root',
    'tags': ['jedi', 'active', 'rebel'],
}

factory = UserFactory()
user = factory.create(testdata)
print user.username  # 'jedi'
print user.joindate  # datetime.date(2012, 1, 18)
print user.emailAddress.email  # 'jedi@rebillion.net'

```

To see how to instruct Devil to automatically convert incoming data into python
objects using factories, see [configuration](#factory).

Factories also support name mangling of properties. For example:

    emailAddress -> email_address
    email_address -> emailAddress

This is achieved by providing ``alias`` property for a field. For Example:

```python

class UserRepresentation(Representation):
    emailAddress = EmailField(alias='email_address')
```

This definition wouldn't have any affect on data when in serialized format. That
is, in JSON or in dictionary the property name is still `emailAddress`. However,
when the field is present in python object (i.e. after object has been created
with `factory.create()` or when it is given to `factory.serialize()`) the name
of the property is `email_address`.


## Auto-generated Documentation

**NOTE** This is still a work in progress but there is a very bare (but working)
implementation in the [doc branch][16].

Basically, by subclassing your resources from `DocumentedResource` instead of
`Resource` you add support for auto- generated documenatation. When client
provides `_doc` in the query string of the request, a documentation is generated
instead of the actual method being executed. The documentation includes:

  - docstring of the implementing resource-class
  - all supported methods and their docstrings
  - representations (if defined) and their constraints


## Configuration

Resources in Devil can be configured by overriding any of the following class
properties defined in the `devil.Resource` class:

```python
class Resource(object):
    access_controller = None
    allow_anonymous = True
    authentication = None
    representation = None
    post_representation = None
    factory = None
    post_factory = None
    default_mapper = None
    mapper = None
```

It is usually a good idea to derive `devil.Resource` and use the derived class
as a base class for your project's resources. That way, you only need to define
these configurations once. The values shown above are the default values that are
used if not overridden.


### representation

When defined, this representation will be used for validating both, incoming and
outgoing data. For example: `representation = UserRepresentation()`. More
information on representations is available [here](#defining-representations)


### post_representation

When defined, this representation will be used for validating client-data inside
a POST request. If not defined `representation` will be used for POST requests
too. `post_representation` will never be used for validating outgoing data (i.e.
data returned to the client).


### factory

When defined, Devil uses this factory to automatically convert incoming data
into python objects and outgoing objects into serialized format. An example
definition looks like this: `factory = UserFactory()`. More information on
factories is available [here ](#using-object-factories).


### post_factory

When defined, this factory will be used for creating a python object from data
inside a POST request. If not defined, `factory` will be used for POST requests
too. `post_factory` will never be used for serializing outgoing data.


### authentication

Defines the authentication handler. When provided, it should be an object that
has a function called `authentication`. This function takes only one
paremeter: the request object. The function should raise
`devil.errors.Unauthorized` if the request cannot be authorized otherwise it
must populate the `request.user` property.

Instead of implementing your own authentication you are free to use devil's
HTTP basic authentication or one of Django's authentication middlewares. To
use Devil's authentication, you can simply add this to your resource class:

```python
from devil.auth import HttpBasic

class MyResource(Resource):
    authentication = HttpBasic()
```


### allow_anonymous

If the resource allows anonymous access, set this to `True` (default). Note,
that this is different from `authentication` as you can turn authentication on
but still allow anonymous access (for example with limited access).


### access_controller

If `access_controller` is set, devil uses it to authorize requests. The value
of `access_controller` must be an object that has a method called
`check_perm`. This method takes two parameters: the request object and the
resource that is being queried. If the request is permitted, the function
should return nothing. However, if the request is not permitted, the function
should raise `devil.errors.Forbidden`.

While you are free to implement your own access controller, devil comes with
an access controller based on Django's _users_, _groups_ and _permissions_. To
make use of it, you would say this in your resource code:


```python
from devil.resource import Resource
from devil.perm.acl import PermissionController

class MyResource(Resource):
    access_controller = PermissionController()
```

After this, all requests to `MyResource` will be authorized based on the user
who sent the request and the method that was used. So, each resource has four
possible permissions associated with it: `post`, `get`, `put` and `delete`.
Devil will automatically check that the user (or the user's group) making the
request has appropriate permission to access the resource.

Devil can automatically add all necessary permissions into the database but
you (or the site administrator) will need to assign these permissions for
users (or groups). To have devil populate all possible permissions into the
database you need to tell devil what are the resources you want to protect and
then use `syncdb` to insert them. For all this, you would first add two things
into your Django `settings.py` file:


  1. `ACL_RESOURCES` to define your protected resources
  2. `devil.perm` among `INSTALLED_APPS`


For example:

```python
ACL_RESOURCES = (
    'myproject.myapp.urls.acl_resources',
    )

INSTALLED_APPS = (
    'devil.perm',
    )
```

Now, you also need to have your protected resources as a list in the `urls.py`
file. For example:

```python
myresource = MyResource()

acl_resources = (
    myresource,
    )

urlpatterns = (
    url(r'^test', myresource),
    )
```

After this, you can run `python manage.py syncdb` and have devil to insert all
necessary permissions into the database. To be exact, devil inserts them into
Django's `auth_permission` table. The format for the permission name is
`prefix_resourcename_method`. The `prefix` is "resource", the `resourcename`
is whatever your resource class´ `name()` function returns and `method` is the
request method (i.e. "post", "get", "put" or "delete"). If you haven't
overridden the `name()` function in your resource class, it returns the name
of the class with CamelCase converted to slashes. So, in our example running
the `syncdb` would generate following four permissions into the database:


  - "`resource_my/resource_post`"
  - "`resource_my/resource_get`"
  - "`resource_my/resource_put`"
  - "`resource_my/resource_delete`"


Now, you are ready to assign these permissions to your users or groups by
using the Django [admin interface][9].

**Few notes:**

  - Devil's access controller depends on the `request.user` property.
    This means that the request must have been authenticated before it
    lands to the access controller. The easiest way to handle
    authentication is to use devil's HTTP basic authentication or one of
    Django's authentication middlewares.
  - `request.user` may not be Django's `AnonymourUser`
  - If the user making the request is a [super user][10], permission is
    always granted.
  - The user needs to be [active][11] in order to get access to any resource
    that is protected by devin's access controller.
  - Devil's access controller uses Django's [get_all_permissions][12] function
    to figure out whether the user has the permission.


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
[8]:https://docs.djangoproject.com/en/dev/topics/http/urls/
[9]:https://docs.djangoproject.com/en/dev/ref/contrib/admin/
[10]:https://docs.djangoproject.com/en/dev/topics/auth/#django.contrib.auth.models.User.is_superuser
[11]:https://docs.djangoproject.com/en/dev/topics/auth/#django.contrib.auth.models.User.is_active
[12]:https://docs.djangoproject.com/en/dev/topics/auth/#django.contrib.auth.models.User.get_all_permissions
[13]:http://wuher.github.com/devil/
[14]:https://github.com/wuher/devil/tree/master/example/userdb
[15]:https://docs.djangoproject.com/en/dev/ref/forms/fields/
[16]:https://github.com/wuher/devil/tree/doc
[17]:https://github.com/wuher/devil/blob/doc/devil/fields/representation.py
[18]:https://github.com/wuher/devil/blob/master/devil/fields/factory.py
