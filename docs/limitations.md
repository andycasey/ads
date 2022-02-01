# Limitations

At the time of writing (1 Februrary 2022) there are known limitations with the data model implementation. Most of these will be overcome with some coding time. Below I describe the reasons for these limitations.

## It's SQL, but not.

We use a SQL-like interface (with SQL expressions) to interface to a document search service that is not SQL. For example, Solr cannot do the same things that SQL can. That means we either need to:
* Intentionally restrict the expressions engine so that it can *only* do what Solr can do. (This could create inconsistencies in what can be given as expressions to ``ads.Document.select().where(...)`` compared to ``ads.Journal.select().where(...)``.
* Re-cast the given expression to include all possible matches from ADS, ingest the results to a temporary SQLite database, and execute the SQL expression on the local database. We already do this for {obj}`ads.Library` because the ADS end-point does not allow us to search for libraries by attribute. But re-casting expressions could be a bit of a rabbit hole: lots of edge cases to consider.


## BigQuery

Solr queries of the form ``bibcode:A OR bibcode:B OR bibcode:C ... `` can be expensive. For this reason, if you are retrieving documents from a list of bibliographic codes (as we do whenever we retrieve documents from a library) then you should use the BigQuery API end point. The ``ads`` package does this automatically for you. If your expression is simple, like ``Document.select().where(Document.in_(library))`` then that's easy enough for ``ads`` to manage.

If the query becomes something complicated that involves multiple large libraries and sub-expressions, then the expression probably won't be parsed correctly. For example, something like this will (probably) fail:

```python
from ads import Document, Library

lib_1 = Library.get(id="...") # some library with 100+ documents
lib_2 = Library.get(id="...") # some library with 100+ documents
lib_3 = Library.get(id="...") # some library with 100+ documents

docs = (
    Document.select()
            .where(
            	(Document.in_(lib_1) & (Document.year == 2020))
            |   (
                    (Document.year == 2021) & Document.in_(lib_2) & Document.not_in(lib_3)
                )
            |   (Document.year == 2019)
            )
)
```

If we parsed this expression directly to the standard Solr end-point we would get three large bibcode comparisons, and Solr would likely fail. If we wanted to send this to the BigQuery endpoint then there are some steps we would have to take, because the BigQuery endpoint takes a list of bibcodes and then runs the expression **after** retrieving those bibcodes. So these are the steps the ``ads`` package would have to take:
1. Call the standard Solr search end-point with just the ``(Document.year == 2019)`` expression, and remove this sub-expression from the rest of the expression.
2. Combine the list of bibliographic codes in ``lib_1``, ``lib_2``, **and** ``lib_3``, even though the expression on ``lib_3`` is ``Document.not_in(lib_3)``.
3. Call BigQuery using the combined list of bibliographic codes and apply the following expression: ``(Documeny.year == 2020) | (Document.year == 2021)``
4. Take all the results from the API calls in Step 1 and 3, put them to an in-memory SQLite database, and re-execute the expression. (Or apply filtering using Python.)

There are a couple of other ways to do this, including three distinct searches for each sub-expression. But the second sub-expression might still require a library operation.

If you get to the stage of building queries like this, you should probably try to:
* Make any library operations first, before a document search, so that you can restrict your expression to include just one library call.
* Be aware of when BigQuery is executed, and how it is executed, so you know when your expression may require multiple searches.


## Metrics

I haven't decided how much effort to put into exposing the ADS metrics service yet.

## Notifications

I haven't built the data model and interface for myADS notifications yet, but it would be a cool thing for you to do in a pull request.