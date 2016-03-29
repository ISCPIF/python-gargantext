#!/bin/bash

# ## CONFIGURE POSTGRESQL

psql -c "CREATE user gargantua WITH PASSWORD 'C8kdcUrAQy66U'" && createdb -O gargantua gargandb

