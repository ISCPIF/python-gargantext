UNIT TESTS
==========

Prerequisite
------------
Running unit tests will involve creating a **temporary test DB** !
 + it implies **CREATEDB permssions** for settings.DATABASES.user  
   (this has security consequences)
 + for instance in gargantext you would need to run this in psql as postgres:  
   `# ALTER USER gargantua CREATEDB;`

A "principe de précaution" could be to allow gargantua the CREATEDB rights on the **dev** machines (to be able to run tests) and not give it on the **prod** machines (no testing but more protection just in case).

Usage
------
```
./manage.py test unittests/ -v 2            # in django root container directory

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
  8. ** tests users ??? **
  9. **tests_090_toolchain**  
      Checks each data source parserbot (CSV, Pubmed, Zotero, Istex, etc.)
      - correct parsing for a small sample



GargTestRunner
---------------
Most of the tests will interact with a DB but we don't want to touch the real one so we provide a customized test_runner class in `unittests/framework.py` that creates a test database.

It must be referenced in django's `settings.py` like this:
```
TEST_RUNNER = 'unittests.framework.GargTestRunner'
```

(This way the `./manage.py test` command will be using GargTestRunner.)


Using a DB session
------------------
The GargTestRunner overrides default settings so that the test database is used in the way we usually do it in gargantext :

**Example**
```
from gargantext.util.db import session

session.query(Nodes).all()   # gives all the nodes of the testdb
```


Accessing the URLS
------------------
Django tests provide a client to browse the urls


**Example**
```
from django.test import Client

class MyTestRecipes(TestCase):
    def setUp(self):
        self.client = Client()

    def test_001_get_front_page(self):
        ''' get the about page localhost/about '''
        # --------------------------------------
        the_response = self.client.get('/about')
        # --------------------------------------
        self.assertEqual(the_response.status_code, 200)
```

Logging in
-----------
Most of our functionalities are only available on login so we provide a fake user at the initialization of the test DB.

His login in 'pcorser' and password is 'peter'

**Example**
```
from django.test import Client

class MyTestRecipes(TestCase):
    def setUp(self):
        self.client = Client()
        # login ---------------------------------------------------
        response = self.client.post(
                      '/auth/login/',
                      {'username': 'pcorser', 'password': 'peter'}
                   )
        # ---------------------------------------------------------

    def test_002_get_to_a_restricted_page(self):
        ''' get the projects page /projects '''
        the_response = self.client.get('/projects')
        self.assertEqual(the_response.status_code, 200)
```

