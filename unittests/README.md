UNIT TESTS
==========

Prerequisite
------------
Running unit tests will involve creating a **temporary test DB** !
 + it implies **CREATEDB permssions** for settings.DATABASES.user  
   (this has security consequences)
 + for instance in gargantext you would need to run this in psql as postgres:  
   `# ALTER USER gargantua CREATEDB;`


Usage
------
From the django container directory to runs all tests type:

```
./manage.py test unittests/ -v 2

# or for a single module
./manage.py test unittests.tests_010_basic  -v 2
```

( `-v 2` is the verbosity level )


Tests
------
  1. **tests_010_basic**
  2. ** tests ??? **
  3. ** tests ??? **
  4. ** tests ??? **
  5. ** tests ??? **
  6. ** tests ??? **
  7. **tests_070_routes**  
     Checks the response types from the app url routes:  
    - "/"
    - "/api/nodes"
    - "/api/nodes/<ID>"


Creating a test DB
------------------
Most of the tests will interact with a DB but we don't want to touch the real one so we provide a customized test_runner class in `unittests/framework.py`

Our custom class needs to be referenced as the `TEST_RUNNER` environment variable in django's `settings.py` like this:
```
TEST_RUNNER = 'unittests.framework.GargTestRunner'
```

Using a DB session
------------------
To emulate a session the way we usually do it in gargantext, our `unittests.framework` also
provides a session object to the test database via `GargTestRunner.testdb_session`

To work correctly, it needs to be imported inside the test setup.

**Example**
```
class MyTestRecipes(TestCase):
    def setUp(self):
        from unittests.framework import GargTestRunner
        session = GargTestRunner.testdb_session
        new_project = Node(
            typename = 'PROJECT',
            name = "hello i'm a project",
        )
        session.add(new_project)
        session.commit()
```


Accessing the URLS
------------------
Django tests provide a client to browse the urls


**Example**
```
class MyTestRecipes(TestCase):
    def setUp(self):
        from django.test import Client
        self.client = Client()

    def test_001_get_front_page(self):
        ''' get the about page localhost/about '''
        the_response = self.client.get('/')
        self.assertEqual(the_response.status_code, 200)
```

Logging in
-----------
Most of our functionalities are only available on login so we provide a fake user at the initialization of the test DB.

His login in 'pcorser' and password is 'peter'

**Example**
```
class MyTestRecipes(TestCase):
    def setUp(self):
        from django.test import Client
        self.client = Client()
        # login with our fake user
        response = self.client.post(
                            '/auth/login/',
                            {'username': 'pcorser', 'password': 'peter'}
                            )

    def test_002_get_to_a_restricted_page(self):
        ''' get the projects page /projects '''
        the_response = self.client.get('/projects')
        self.assertEqual(the_response.status_code, 200)
```
