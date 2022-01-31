# Upgrading from 0.12.3

If you've used Version 0.12.3 of the ``ads`` code then you might need to make some changes to your script to make sure it still runs with Version 1 of the ``ads`` package. I have tried to make things backwards-compatible everywhere I can, but sometimes that is an unachievable goal. This page documents the main user-facing changes you need to know about.

## Unlimited documents!

In version 0.12.3 [the default number of records to return was 50](https://github.com/andycasey/ads/blob/7939be2650bfee85be13cd46cfa2e037381da7fc/ads/search.py#L352): 1 page with 50 rows.

In version 1 there is no limit on the number of records when you use the {obj}`ads.Document.select` function. You'll keep getting documents until ADS stops sending them. That means **you should set an upper limit for how many records you want**, or `.count()` the number of records returned before iterating over them.

:::{important}
This is **especially** true if you are using asynchronous coroutines to perform searches. If you don't place a limit on the number of records, then as soon as a single page is returned and the number of documents found is known, ``ads`` is going to open up a lot of asynchronous connections to the ADS server to retrieve all the results you have asked for! 

Be a good user: always set a limit.
:::


## ``ads.Article`` is now ``ads.Document``

The ``ads.Article`` class no longer exists. It has been replaced with ``ads.Document``. So if you have any ``isinstance(doc, ads.Article)`` calls then these will fail.


## ``ads.SearchQuery`` still exists

Because people would get mad if it didn't exist. But it's not recommended: you should use the ``ads.Document.select()`` methods instead. 

The ``ads.SearchQuery`` object has the same callable interface that it did in 0.12.3, but it now returns a ``ModelSelect`` object. You won't notice any difference if you are just using ``list(ads.SearchQuery(...))``, or if you are iterating over your ``ads.SearchQuery`` results, but if you are doing something fancier then you might have problems.

## By default you get all fields

If you use ``ads.SearchQuery`` then by default you will retrieve just five fields from ADS (author, bibcode, id, year, title), which is the same behaviour in version 0.12.3.

If you use ``ads.Document.select()`` (as-is) or ``ads.Document.get()`` then you will retrieve **all** fields from ADS.

## Lazy loading still exists, but it's explicitly discouraged

Lazy loading solves the following situation: you asked ADS for fields ``Y``, and ``Z``, and then moments later you decide you want field ``X`` on a document you have just retrieved. When that happens, ``ads`` notices that you don't have this data field and it will ask ADS **just** for this missing field. That's good if you are doing things interactively and it's only for a few fields or documents. But if you're doing this for many fields, or for a single field for many documents, then you will quickly reach your API rate limits. 

In version 0.12.3 by default you would only get a few fields back, and anything else you wanted would be lazily-loaded. By default **all** ADS fields will be requested when you use ``ads.Document.select()``. 
Lazy loading should only ever occur if you explicitly specified which fields you want (e.g., ``Document.select(Document.author, Document.bibcode)``) and you need a field that you didn't request (e.g., ``Document.title``). You will see a single warning about this.


## The ``ads.Article.bibtex`` is gone

This was a (cached) property that would use the [ADS export service](services/export.md) to generate a BiBTeX entry for a document. This no longer exists, in part because it's a little silly to use an API call to the export service for just a single document, when this service can accept many documents at once. And with the {obj}`ads.services.export.bibtex` function you can specify optional keyword arguments to alter the presentation of your citation.

Here's an example:

```python
# OLD WAY, no longer exists:
citation = document.bibtex

# NEW WAY
from ads.services import export
citation = export.bibtex(
    document,
    max_author=3,
    journal_format=1,
    key_format="%1H:%Y"
)
```


## The ``ads.Article.metrics`` is gone

:::{todo}
Haven't decided how to expose metrics service yet.
:::

## The ``ads.Article.citation`` is gone

Use this instead:

```python
from ads import Document

# Get a random document.
doc = Document.get()

# OLD WAY, no longer exists. This only gave bibcodes!
cited_bibcodes = doc.citation

# NEW WAY, gives you ads.Document objects!
cited_document_objects = Document.select().where(Document.citations(doc))
```

## The ``ads.Article.reference`` is gone

Use this instead:

```python
from ads import Document

# Get a random document.
doc = Document.get()

# OLD WAY, no longer exists. This only gave bibcodes!
referenced_bibcodes = doc.reference

# NEW WAY, gives you ads.Document objects!
referenced_document_objects = Document.select().where(Document.references(doc))
```
