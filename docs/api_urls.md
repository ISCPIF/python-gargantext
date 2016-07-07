List of garg's own JSON API(s) urls
===================================

2016-05-27

### /api/nodes/2

```
{
  "id": 2,
  "parent_id": 1,
  "name": "abstract:\"evaporation+loss\"",
  "typename": "CORPUS"
}
```
------------------------------

### /api/nodes?pagination_limit=-1
```
{
  "records": [
    {
      "id": 9,
      "parent_id": 2,
      "name": "A recording evaporimeter",
      "typename": "DOCUMENT"
    },
    (...)
    {
      "id": 119,
      "parent_id": 81,
      "name": "GRAPH EXPLORER COOC (in:81)",
      "typename": "COOCCURRENCES"
    }
  ],
  "count": 119,
  "parameters": {
      "formated": "json","pagination_limit": -1,
      "fields": ["id","parent_id","name","typename"],
      "pagination_offset": 0
  }
}
```
------------------------------

### /api/nodes?types[]=CORPUS
```
{
  "records": [
    {
      "id": 2,
      "parent_id": 1,
      "name": "abstract:\"evaporation+loss\"",
      "typename": "CORPUS"
    },
    (...)
    {
      "id": 8181,
      "parent_id": 1,
      "name": "abstract:(astrogeology+OR ((space OR spatial) AND planetary) AND geology)",
      "typename": "CORPUS"
    }
  ],
  "count": 2,
  "parameters": {
        "pagination_limit": 10,
        "types": ["CORPUS"],
        "formated": "json",
        "pagination_offset": 0,
        "fields": ["id","parent_id","name","typename"]
  }
}
```
------------------------------
### /api/nodes/5?fields[]=ngrams

Où <5> représente un doc_id ou list_id

```
{
  "ngrams": [
    [1.0,{"id":2299,"n":1,"terms":designs}],
    [1.0,{"id":1917,"n":1,"terms":height}],
    [1.0,{"id":1755,"n":2,"terms":higher speeds}],
    [1.0,{"id":1940,"n":1,"terms":cylinders}],
    [1.0,{"id":2221,"n":3,"terms":other synthesized materials}],
    (...)
    [2.0,{"id":1970,"n":1,"terms":storms}],
    [9.0,{"id":1754,"n":2,"terms":spherical gauges}],
    [1.0,{"id":1895,"n":1,"terms":direction}],
    [1.0,{"id":2032,"n":1,"terms":testing}],
    [1.0,{"id":1981,"n":2,"terms":"wind effects"}]
  ]
}
```
------------------------------

### api/nodes/3?fields[]=id&fields[]=hyperdata&fields[]=typename
```
{
  "id": 3,
  "typename": "DOCUMENT",
  "hyperdata": {
    "language_name": "English",
    "language_iso3": "eng",
    "language_iso2": "en",
    "title": "A blabla analysis of laser treated aluminium blablabla",
    "name": "A blabla analysis of laser treated aluminium blablabla",
    "authors": "A K. Jain, V.N. Kulkarni, D.K. Sood"
    "authorsRAW": [
    {"name": "....", "affiliations": ["... Research Centre,.. 085, Country"]},
    {"name": "....", "affiliations": ["... Research Centre,.. 086, Country"]}
    (...)
    ],
    "abstract": "Laser processing of materials, being a rapid melt quenching process, quite often produces a surface which is far from being ideally smooth for ion beam analysis. (...)",
    "genre": ["research-article"],
    "doi": "10.1016/0029-554X(81)90998-8",
    "journal": "Nuclear Instruments and Methods In Physics Research",
    "publication_year": "1981",
    "publication_date": "1981-01-01 00:00:00",
    "publication_month": "01",
    "publication_day": "01",
    "publication_hour": "00",
    "publication_minute": "00",
    "publication_second": "00",
    "id": "61076EB1178A97939B1C893904C77FB7DA2276D0",
    "source": "elsevier",
    "distributor": "istex"
  }
}
```

## TODO continuer la liste
