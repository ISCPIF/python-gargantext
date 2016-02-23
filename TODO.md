# Projects

## Overview of all projects

- re-implement deletion

## Single project view

- re-implement deletion


# Taggers

Path for data used by taggers should be defined in `gargantext.constants`.


# Database

# Sharing

Here follows a brief description of how sharing could be implemented.

## Database representation

The database representation of sharing can be distributed among 4 tables:
 - `persons`, of which items represent either a user or a group
 - `relationships` describes the relationships between persons (affiliation
     of a user to a group, contact between two users, etc.)
 - `nodes` contains the projects, corpora, documents, etc. to share (they shall
     inherit the sharing properties from their parents)
 - `permissions` stores the relations existing between the three previously
     described above: it only consists of 2 foreign keys, plus an integer
     between 1 and 3 representing the level of sharing and the start date
     (when the sharing has been set) and the end date (when necessary, the time
     at which sharing has been removed, `NULL` otherwise)

## Python code

The permission levels should be set in `gargantext.constants`, and defined as:
```python
PERMISSION_NONE = 0     # 0b0000
PERMISSION_READ = 1     # 0b0001
PERMISSION_WRITE = 3    # 0b0011
PERMISSION_OWNER = 7    # 0b0111
```

The requests to check for permissions (or add new ones) should not be rewritten
every time. They should be "hidden" within the models:
 - `Person.owns(node)` returns a boolean
 - `Person.can_read(node)` returns a boolean
 - `Person.can_write(node)` returns a boolean
 - `Person.give_right(node, permission)` gives a right to a given user
 - `Person.remove_right(node, permission)` removes a right from a given user
 - `Person.get_nodes(permission[, type])` returns an iterator on the list of
    nodes on which the person has at least the given permission (optional
    argument: type of requested node)
- `Node.get_persons(permission[, type])` returns an iterator on the list of
   users who have at least the given permission on the node (optional argument:
   type of requested persons, such as `USER` or `GROUP`)

## Example

Let's imagine the `persons` table contains the following data:

| id | type  | username  |
|----|-------|-----------|
| 1  | USER  | David     |
| 2  | GROUP | C.N.R.S.  |
| 3  | USER  | Alexandre |
| 4  | USER  | Untel     |
| 5  | GROUP | I.S.C.    |
| 6  | USER  | Bidule    |

Assume "David" owns the groups "C.N.R.S." and "I.S.C.", "Alexandre" belongs to
the group "I.S.C.", with "Untel" and "Bidule" belonging to the group "C.N.R.S.".
"Alexandre" and "David" are in contact.
The `relationships` table then contains:

| person1_id | person2_id | type    |
|------------|------------|---------|
| 1          | 2          | OWNER   |
| 1          | 5          | OWNER   |
| 3          | 2          | MEMBER  |
| 4          | 5          | MEMBER  |
| 6          | 5          | MEMBER  |
| 1          | 3          | CONTACT |

The `nodes` table is populated as such:

| id | type     | name                 |
|----|----------|----------------------|
| 12 | PROJECT  | My super project     |
| 13 | CORPUS   | A given corpus       |
| 13 | CORPUS   | The corpus           |
| 14 | DOCUMENT | Some document        |
| 15 | DOCUMENT | Another document     |
| 16 | DOCUMENT | Yet another document |
| 17 | DOCUMENT | Last document        |
| 18 | PROJECT  | Another project      |
| 19 | PROJECT  | That project         |

If we want to express that "David" created "My super project" (and its children)
and wants everyone in "C.N.R.S." to be able to view it, but not access it,
`permissions` should contain:

| person_id | node_id | permission |
|-----------|---------|------------|
| 1         | 12      | OWNER      |
| 2         | 12      | READ       |

If "David" also wanted "Alexandre" (and no one else) to view and modify "The
corpus" (and its children), we would have:

| person_id | node_id | permission |
|-----------|---------|------------|
| 1         | 12      | OWNER      |
| 2         | 12      | READ       |
| 3         | 13      | WRITE      |

If "Alexandre" created "That project" and wants "Bidule" (and no one else) to be
able to view and modify it (and its children), the table should then have:

| person_id | node_id | permission |
|-----------|---------|------------|
| 3         | 19      | OWNER      |
| 6         | 19      | WRITE      |
