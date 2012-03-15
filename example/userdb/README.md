# UserDB example

This example demonstrates how to create a single `user` resource that supports
adding, updating, listing and deleting user resources. For the sake of
simplicity the user representation only has two fields `name` and `age`. For
example:

    {
        "name": "Shmi Skywalker",
        "age": 55
    }

The API is mapped to URL `/user/` and supports all four methods like so:

    GET /user/
    GET /user/1
    POST /user/
    PUT /user/1
    DELETE /user/1

You can start the application by navigating into `examples/userdb` and saying:

    $ python manage.py syncdb
    $ python manage.py runserver

You can now test the api by issuing HTTP requests to above mentioned URLs. For
example:

    $ curl http://localhost:8000/user
    $ curl -v http://localhost:8000/user/ -X POST -d '{"name": "Luke Skywalker", "age": 44}' -H 'Content-Type: application/json'
    $ curl http://localhost:8000/user/1
    $ curl -v http://localhost:8000/user/1 -X PUT -d '{"name": "Luke Skywalker", "age": 33}' -H 'Content-Type: application/json'
    $ curl http://localhost:8000/user/1
    $ curl -v http://localhost:8000/user/1 -X DELETE
    $ curl http://localhost:8000/user


The actual implementation can be found in the `api/resources.py` file. In that
file you can see the implementation of all four methods
(`post/get/put/delete`).

The project was created as any other Django project by saying `django-admin
startproject userdb` and `python manage.py startapp api`. After this following
modifications were made:

  1. Add datababase configuration, our application and strip
  unnecessary applicationa and middlewares from `settings.py`. See
  following configuration keys in the settings file for details:
  `DATABASES`, `MIDDLEWARE_CLASSES`, `INSTALLED_APPS`.
  2. Implement models. You can see the file `api/models.py` for details.
  3. Implement the user resource. You can see the file `api/resources.py`
  for details.
  4. Create the URL mapping. You can see the file `urls.py` for details.

All tests are implemented in the file `api/tests.py`. You can run them (by
Django convention) by saying `python manage.py test api`.

