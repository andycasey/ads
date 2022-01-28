# Documents


## The {obj}`ads.Document` object

The {obj}`ads.Document` object is used to represent a record in ADS. We use this data model and an [object-relational mapper](https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping) (ORM) to search and filter for documents on ADS in a programmatic way. For example, you can write queries like 
```python
expression = (Document.year < 2020) & Document.title.like("JWST")
```
and have them translated into a (Solr) query that you would input through the ADS web interface.

### Fields and operators

The ADS search engine has some fields and operators that are searchable but not viewable. That means you can search for documents using this field, but when you retrieve a document that field will be `None`.

The {obj}`ads.Document` data model reflects this functionality as closely as possible by using:

 - typed fields for searchable and viewable Solr fields
    + *for example, {obj}`ads.Document.id` is an `IntegerField`*
 - virtual fields for those that are searchable but not viewable, and
    + *for example, {obj}`ads.Document.ack` is a `VirtualField`*
 - functions for Solr operators.
    + *for example, {func}`ads.Document.similar`*.

:::{tip}
All typed fields, virtual fields, and functions can be accessed as attributes of the {obj}`ads.Document` object. 

That means if you're using an interactive Python environment (e.g., a python shell, an iPython shell, or Jupyter) then you can access all of these by typing ``ads.Document`` and using :kbd:`<tab>` completion.
:::

The following fields can be **searched and viewed**:

```{eval-rst}
.. autosummary::
    :nosignatures:

    ads.Document.abstract
    ads.Document.aff
    ads.Document.aff_id
    ads.Document.alternate_bibcode
    ads.Document.alternate_title
    ads.Document.arxiv_class
    ads.Document.author
    ads.Document.author_count
    ads.Document.author_norm
    ads.Document.bibcode
    ads.Document.bibgroup
    ads.Document.bibstem
    ads.Document.citation_count
    ads.Document.cite_read_boost
    ads.Document.data
    ads.Document.database
    ads.Document.date
    ads.Document.doctype
    ads.Document.doi
    ads.Document.eid
    ads.Document.email
    ads.Document.entry_date
    ads.Document.esources
    ads.Document.facility
    ads.Document.grant
    ads.Document.grant_agencies
    ads.Document.grant_id
    ads.Document.id
    ads.Document.identifier
    ads.Document.indexstamp
    ads.Document.isbn
    ads.Document.issn
    ads.Document.issue
    ads.Document.keyword
    ads.Document.lang
    ads.Document.links_data
    ads.Document.nedid
    ads.Document.nedtype
    ads.Document.orcid_other
    ads.Document.orcid_pub
    ads.Document.orcid_user
    ads.Document.page
    ads.Document.page_count
    ads.Document.property
    ads.Document.pub
    ads.Document.pub_raw
    ads.Document.pubdate
    ads.Document.simbid
    ads.Document.simbtype
    ads.Document.read_count
    ads.Document.title
    ads.Document.vizier
    ads.Document.volume
    ads.Document.year
```

:::{important}
Just because a field is viewable doesn't mean you will always get a value. For example, if a record has no email address information about the authors, then `doc.email` will return something like `['-', '-']` for a two-author record. In other situations the value returned might just be `None`.
:::

&nbsp;

These **virtual fields** can be searched, but not viewed:


```{eval-rst}
.. autosummary::
    :nosignatures:

    ads.Document.abs
    ads.Document.all
    ads.Document.arxiv
    ads.Document.full
    ads.Document.orcid
```

&nbsp;


These functions access **Solr operators** to search for documents, but don't return a value:


```{eval-rst}
.. autosummary::
    :nosignatures:

    ads.Document.citations
    ads.Document.citis
    ads.Document.classic_relevance
    ads.Document.instructive
    ads.Document.join_citations
    ads.Document.join_references
    ads.Document.pos
    ads.Document.references
    ads.Document.reviews
    ads.Document.similar
    ads.Document.top_n
    ads.Document.trending
    ads.Document.useful
```

The {obj}`ads.Document.useful2` and {obj}`ads.Document.reviews2` operators are also available, but 'not' listed here to avoid confusion.

## Search for documents

The {obj}`ads.Document` has a {func}`ads.Document.select` function to select (search for) documents. If you've used a SQL database before, you'll notice this approach is very similar to how you would select records from a SQL database. 

When you call {obj}`ads.Document.select` it returns a `ModelSelect` object. This object has everything it needs to perform the ADS search, but it won't actually do anything until you try to access documents (e.g., by iterating over the `ModelSelect` object). For example:

```python
from ads import Document

# The .where() and .limit() functions will be explained below. 
docs = (
    Document.select()
            .where(
                Document.author == "Ness, M"
            )
            .limit(3)
)

print(f"# {type(docs)}")
# <class 'ads.ModelSelect'>

# *Nothing* has been sent to ADS yet.
# The request is only executed when we try to access the results:
for doc in docs: # Now the request is made to ADS
    print(f"# {doc}")
# <Document: bibcode=2017AJ....154...28B>
# <Document: bibcode=2018ApJS..235...42A>
# <Document: bibcode=2017ApJS..233...25A>
```

We can access (or iterate over) the documents ``docs`` as many times as we want, but the query is only executed to ADS once.

### Select fields

If you only want specific fields returned by ADS, you can explicitly give these to {func}`ads.Document.select`. If you want all the fields of a document then don't supply anything to `.select()`.  For example:

```python
from ads import Document

# Give me everything (this is the usual case).
everything = Document.select()

# I only want bibcodes, author counts, and citation counts.
something = Document.select(
    Document.bibcode, Document.author_count, Document.citation_count
)
```

If you made the second query above (``something``) and then later decided you also needed the title of a document (or some other field), don't worry: the data attributes on {obj}`ads.Document` are *special* and will lazily retrieve the missing data for you. This is considered bad practice because it increases the number of API calls you use, and for this reason you will see a (single) warning. 

Note that even if we select only single field, when we iterate over {func}`ads.Document.select` we will always get a {obj}`ads.Document` object. Below is an example. The input Python code is shown in the first tab, and the second tab shows the output.

``````{tab} Python
```python
from ads import Document

# Give me citation counts for these documents
docs = (
    Document.select(
                Document.citation_count,
            ).where(
                Document.bibcode.in_(["1996PhRvL..77.3865P", "1996PhRvB..5411169K"])
            )
)

for doc in docs:
    # Oh shit, I want their titles too.
   print(f"{doc.bibcode}: {doc.title[0]} ({doc.citation_count:,} citations)")
```
``````
``````{tab} Output
```bash
LazyAttributesWarning: You're lazily loading document attributes, which makes many calls to the API. This will impact your rate limits. If you know what document fields you want ahead of time, provide them as arguments to `Document.select()`.

1996PhRvL..77.3865P: Generalized Gradient Approximation Made Simple (61,563 citations)
1996PhRvB..5411169K: Efficient iterative schemes for ab initio total-energy calculations using a plane-wave basis set (34,986 citations)
```
``````


The {obj}`ads.Document.bibcode` and {obj}`ads.Document.id` will *always* be requested by {obj}`ads.Document.select`, even if you didn't ask for them, because these fields are required to make future queries against ADS, and to evaluate whether two documents are different.

:::{important}
If you're only lazily loading a few fields, or a single field for a few documents, then that's OK. But you should know that **lazy loading a single field in a single document requires an API call**. If you are lazily loading 5 fields in 10 documents, that's 50 API calls. For contrast, a single API call to the ADS search service can return 200 documents with *all fields*. 

Lazy loading is a feature to help you code interactively without having to repeat complex searches, but it is not intended to be used often.
:::


### Filtering

By default, {func}`ads.Document.select` on it's own would return an iterable that would (eventually) retrieve **every** document from ADS. That's probably not what you want; you should provide some filter to return particular documents.

The way we filter for documents is by using the `.where()` function with {func}`ads.Document.select()`. Here is an example:

```python
from ads import Document

docs = (
    Document.select()
            .where(Document.year == 2015)
)
```

We can combine multiple filters using the standard ``&`` (meaning 'and') and ``|`` (meaning 'or') operators in Python. For example, let's look for documents authored by "Lastname, First" in 2015 or 2018-2019:

```python
from ads import Document

docs = (
    Document.select()
            .where(
                (Document.author == "Lastname, First")
            &   (
                    Document.year.between(2018, 2019)
                |   (Document.year == 2015)
                )
            )
)
```

You can include any **searchable** field in the expression you give to ``.where()``. You can also include operators, which are accessible as functions:

```python
from ads import Document

docs = (
    Document.select()
            .where(
                Document.trending(Document.title == "exoplanets")
            &   Document.author_count.between(1, 5)
            )
)
```

:::{important}
Although you may be tempted to use python's ``in``, ``and``, ``or``, and ``not`` operators in your query expressions, these **will not work**.
The return value of an ``in`` expression is always coerced to a boolean value by Python. Similarly, ``and``, ``or``, and ``not`` all treat their arguments as boolean values and cannot be overloaded. So as a guide:
* Use ``|`` instead of ``or``
* Use ``&`` instead of ``and``
* Use ``~`` instead of ``not``
* Use ``.in_()`` and ``.not_in()`` instead of ``in`` and ``not in``

You should always wrap each expression in brackets, too. This is [because of the way Python treats operator precedence](https://github.com/coleifer/peewee/issues/769). That means:

* **Good**: ``(Document.year == 2000) & (Document.title.like("JWST"))``
* **Bad**: ``Document.year == 2000 & Document.title.like("JWST")``
:::

### Ordering

The default ordering for documents returned by ADS is by relevance (computed by the ADS search engine). Instead, you can sort by any of the following fields:

```{eval-rst}
.. autosummary::
    :nosignatures:

    ads.Document.id
    ads.Document.author_count
    ads.Document.bibcode
    ads.Document.citation_count
    ads.Document.date
    ads.Document.entry_date    
```

:::{todo}
first_author, citation_count_norm, score, classic_factor, read_count
:::

Use the `.order_by()` function to order results:

```python
from ads import Document

# Get the freshest bangerz
docs = (
    Document.select()
            .order_by(
                Document.entry_date.desc()
            )
)

# Sort by multiple ordered fields
docs = (
    Document.select()
            .order_by(
                Document.author_count.desc(),
                Document.citation_count.asc()
            )
)
```

### Limits

It's good practice to set a limit for the number of documents you want. This reduces the load on the ADS search service, and it helps the ``ads`` package to paginate queries ahead of time.

Most of the search examples we have shown so far don't have any limits applied. That means they will return *every* document found by ADS that matches the expression.

We can limit the number of documents retrieved by applying a `.limit()` to our `.select()` call:

```python
from ads import Document

docs = (
    Document.select()
            .where(
                (Document.year > 2020)
            )
            .order_by(
                Document.citation_count.desc()
            )
            .limit(10)
)

# Or if we have no filters or sort:
docs = Document.select().limit(3)
```


## Advanced document searches

You can search for documents using expressions that include other data model objects. For example:

* [Search for documents by affiliation](affiliation.md#using-affiliations-in-search)
* [Search for documents by journal](journal.md#search-for-documents-by-journal)
* [Search for documents in a library](library.md#search-for-documents-in-a-library)

## Use explicit Solr queries

If all of this search syntax with `Document.select()` and `.where()` and `.order_by()` and `.limit()` is too frightening or confusing, you can always give an explicit search query to ADS. The way to do this is the same as how you performed searches in previous versions of the ``ads`` package, in order to remain as backwards-compatible as possible.

Here's how you would give an explicit search query:
```
from ads import Document, SearchQuery

docs = SearchQuery(
    q="author:'Ness, M' AND year:2018", 
    fl=["bibcode", "title", "author", "citation_count"]
)

# SearchQuery will return a `ModelSelect` object, 
# which you can use the same as a `ads.ModelSelect` object
for doc in docs:
    print(doc)

# Here's the same query in the "new" way, except we retrieve all fields
docs = (
    Document.select()
            .where(
                (Document.author == "Ness, M")
            &   (Document.year == 2018)
            )
)
```

If you're upgrading from ``ads`` 0.12.3 then your existing code *might* still work, but you'll notice some name changes. For example, when you iterate over a function call of `ads.SearchQuery` you will get {obj}`ads.Document` objects, not `ads.Article` objects. If you have trouble replicating your existing queries in the new search format, please [create an issue on GitHub](https://github.com/andycasey/issues/new).

## BigQuery

Most ADS searches use the [`/search/query` API endpoint](http://adsabs.github.io/help/api/api-docs.html#get-/search/query). However, if the search requires checking for a large number of explicit bibcodes, this can be expensive for the ADS search service. In these situations you should probably use the [`/search/bigquery` API endpoint](http://adsabs.github.io/help/api/api-docs.html#post-/search/bigquery). The ``ads`` package automatically evaluates the expression given to {obj}`ads.Document.select().where()` and decides whether it should use the standard search endpoint, or the BigQuery endpoint. As a user, you don't have to explicitly set this.

The only reason why you need to know about this is that the BigQuery API endpoint has a lower rate limit than the standard search API endpoint, which means you can't make as many BigQuery API calls as you can make standard search calls. So if you run into an error where you have hit your API call limit for the day, but you don't think you have made that many queries, it might be because you have hit the BigQuery API limit, but not the standard search limit.
