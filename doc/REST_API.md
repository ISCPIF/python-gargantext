# Gargantext Light REST-API

There are two REST endpoints for the time being. First the Python backend which
takes care of authentication by delivering JSON Web Tokens, and which will
expose routes to create text corpora, handle ngram lists, build graphs, etc.
Secondly PostgREST, wich exposes database views through its own REST interface.
Those views always provide a read access to gargantext data, and sometimes
a write access. Permissions are handled at database-level, when a user
has no read rights for specific nodes, they are just not returned, they are
"invisible" to this user. When attempting to write on unauthorized nodes, an
error should be returned.

For the development phase those two endpoints are accessible through
<https://dev.gargantext.org/light/> and
<https://dev.gargantext.org/postgrest/>.

## Python Django backend

Prefix on dev: `/light/`

For example: <https://dev.gargantext.org/light/api/auth/token>

### Authentication

#### Get a JSON Web Token

See <https://dev.gargantext.org/light/api/auth/token>.

### ...

[Work in progress]

## PostgREST backend

Current version: 4.4

Prefix on dev: `/postgrest/`

For example: <https://dev.gargantext.org/postgrest/nodes?type=eq.1>

General documentation to query PostgREST endpoint:
<https://postgrest.com/en/v4.4/api.html>.

HTTP status codes returned by PostgREST:
<https://postgrest.com/en/v4.4/api.html#http-status-codes>

Database is not exposed directly, data is accessible through dedicated views
located in a separated PostgreSQL schema.

### Nodes

View name: `nodes`

Nodes are the main entities to represent data in gargantext. Each node have a
parent, except USER nodes. Node can also be related between them by a
many-to-many relationship, and can be related to ngrams in three different ways
(to be detailed later).

This view provides a read and write access. When inserting new nodes (`POST`
verb) some fields are mandatory and some others have default values. See
[below](#nodes-view-schema) for more details. Please remember that database
will not automagically enforce all conventions and constraints of the
gargantext data model, such as node relationships (ie. a PROJECT node must
be the child of a USER node, a CORPUS node must be the child a PROJECT node,
etc.).

#### Types

For the moment there are 18 types of nodes, some are subject to changes,
here are the 4 main types which are not likely to change anytime soon.

|  Type id | Type name |
| -------: | :-------- |
|        1 | USER      |
|        2 | PROJECT   |
|        3 | CORPUS    |
|        4 | DOCUMENT  |

#### Nodes view schema

When querying the nodes view (or related views such as documents), each node
is represented as a JSON object with these fields:

|          Field | JSON type            | Required at insertion  | Description                                                                  |
| -------------: | :------------------- | :--------------------- | :--------------------------------------------------------------------------- |
|             id | int                  | Automatic*             | Unique id of this node                                                       |
|           type | int                  | Yes                    | [Type id](#types) of this node                                               |
|        user_id | int                  | Default = current user | Owner id of this node (an internal id, **not** the id of its USER node)      |
|      parent_id | int                  | Yes                    | Node id of this node's parent                                                |
|           name | string               | Default = empty string | Label of this node, can be used for different purposes depending on its type |
|        created | datetime as a string | Default = now          | Creation date of this node                                                   |
|           data | object               | Default = {}           | [Hyperdata](#hyperdata) of this node                                         |
| title_abstract | string               | Automatic*             | Only meaningful for DOCUMENT nodes: full-text index on title + abstract      |

\* Please don't provide any value, database will generate one automatically.

#### Hyperdata

Type specific data of each node is stored in the `data` field, as a JSON
object. For example documents abstract and title are stored here. There is no
strict schema, a documentation for each type and field remains to be written.

Here is an excerpt of a document `data` field:

    {
        "id": "RePEc:taf:quantf:v:2:y:2002:i:1:p:24-30",
        "url": "http://www.tandfonline.com/doi/abs/10.1088/1469-7688/2/1/302",
        "type": "article",
        "title": "Variance reduction for Monte Carlo simulation in a stochastic volatility environment",
        "source": "Quantitative Finance",
        "authors": "Jean-Pierre Fouque, Tracey Andrew Tullie",
        "abstract": "We propose a variance reduction method for Monte Carlo computation of option prices in the context of stochastic volatility.  This method is based on importance sampling using an approximation of the option price obtained by a fast mean-reversion expansion introduced in Fouque et al (2000 Derivatives in Financial Markets with Stochastic Volatility (Cambridge: Cambridge University Press)). We compare this with the small noise expansion method proposed in Fournie et al (1997 Asymptotic Anal. 14 361-76) and demonstrate numerically the efficiency of our method, in particular in the presence of a skew.",
        "publication_date": "2017-12-22 12:45:10+00:00",
        ...
    }

#### Fetch USER node of `User(id=<user_id>)`

    /nodes?type=eq.1&user_id=eq.<user_id>

#### Fetch all main nodes belonging to `User(id=<user_id>)`

    /nodes?type=in.(1,2,3,4)&user_id=eq.<user_id>

### Documents

View name: `documents`

DOCUMENT [nodes](#nodes-view-schema) with an additional field `ngram_count`
which is the number of ngrams of the document selected in its corpus MAPLIST
("Map terms" in the "Terms" tab of legacy gargantext).

This view is read-only.

#### Fetch documents from `CorpusNode(id=<corpus_id>)`

    /documents?parent_id=eq.<corpus_id>

#### Search for `<query>` in documents from `CorpusNode(id=<corpus_id>)`

    /documents?parent_id=eq.<corpus_id>&title_abstract=fts(english).<query>

NOTICE: before postgrest 4.4 use `english.fts` instead of `fts(english)`.
