# Journals

Every document in ADS that appears in a peer-reviewed journal will have a bibliographic code (bibcode) that includes an abbreviation of the journal name. The bibliographic code is a 19 character string and follows the syntax `YYYYJJJJJVVVVMPPPPA`, where:

- `YYYY`: Year of publication
- `JJJJJ`: A standard abbreviation for the journal (e.g. ApJ, AJ, MNRAS, Sci, PASP, etc.). [A list of abbreviations is available](https://adsabs.harvard.edu/abs_doc/journals1.html#).
- `VVVV`: The volume number (for a serial) or an abbreviation that specifies what type of publication it is (e.g. conf for conference proceedings, meet for Meeting proceedings, book for a book, coll for colloquium proceedings, proc for any other type of proceedings).
- `M`: Qualifier for publication:
    - `E`: Electronic Abstract (usually a counter, not a page number)
    - `L`: Letter
    - `P`: Pink page
    - `Q-Z`: Unduplicating character for identical codes
- `PPPP`: Page number. Note that for page numbers greater than 9999, the page number is continued in the m column.
- `A`: The first letter of the last name of the first author.

You can [read more about bibliographic codes here](https://ui.adsabs.harvard.edu/help/actions/bibcode). 

When the `ads` Python package is first installed, a local SQLite database is created that stores the names and abbreviations of journals, as well as [curated affiliations](affiliations). You can access the records from this local database in the same way that you would access a {class}`ads.Document` or {class}`ads.Library`.

You will need the following imports in order to execute all code blocks on this page:
```python
from ads import Document, Journal
```

## The `Journal` data model

The {class}`ads.Journal` data model contains only two fields:

- {obj}`ads.Journal.abbreviation`: the five character standard abbreviation for the journal (e.g., ApJ)
- {obj}`ads.Journal.title`: the full title of the journal (e.g., _The Astrophysical Journal_)

## Selecting journals

You can select a single `Journal` object with the {func}`ads.Journal.get` method, or select multiple records using the {func}`ads.Journal.select` method. Here are a few examples:

```python
# Retrieve a single journal based on an exact expression.
mnras = Journal.get(abbreviation="MNRAS")

# Get a single journal, but we don't care which one.
journal = Journal.get()

# List every journal with a title containing "astro" (case-insensitive),
# and sort by reverse abbreviation.
astro_journals = Journal.select()\
                        .where(Journal.title.contains("astro"))\
                        .order_by(Journal.abbreviation.desc())
```

## Using journals in search

The primary use for the {class}`ads.Journal` object is to allow for more complex document searches. 

When you use a {class}`ads.Journal` object as an expression in `ads.Document.select().where()`, the
{class}`ads.Journal` object will be resolved to search for the `bibstem` of the journal abbreviation.
This happens automatically, without the need for explicit joins between the {class}`ads.Document` and
{class}`ads.Journal` data models, even if your query on {class}`ads.Journal` is complex.

For example, let's say we wanted to search for documents published in any journal with a title that 
contains the word 'gravitation'. First let's see which journals match this phrase:

```python
for journal in Journal.select().where(Journal.title.contains("gravitation")):
    print(f"> {journal.abbreviation}: {journal.title}")

> GReGr: General Relativity and Gravitation
> GrCo: Gravitation and Cosmology
> JGrPh: Journal of Gravitational Physics
> StHCG: Studies in High Energy Physics Cosmology and Gravitation
```

If we wanted to search ADS for documents in these journals we would normally have to construct a
search phrase like:

```python
q = "bibstem:GReGr OR bibstem:GrCo OR bibstem:JGrPh OR bibstem:StHCG"
# or
q = "bibstem:(GReGr OR GrCo OR JGrPh OR StHCG)
```

But we don't have to do that, because the {class}`ads.Journal` and {class}`ads.Document` data
models know about each other, and know how to resolve relationships between each other in any
expression. Instead we can simply search by the {obj}`ads.Document.journal` attribute:

```python
# Search ADS for documents in gravitation journals
docs = Document.select()\
               .where(Document.journal.title.contains("gravitation"))


# Search for ApJ papers
apj = Journal.get(abbreviation="ApJ")
docs = Document.select()\
               .where(Document.journal == apj)
# or
docs = Document.select()\
               .where(Document.journal.abbreviation == "ApJ")
# or
docs = Document.select()\
               .where(Document.journal.title == "The Astrophysical Journal")


# You can use the Document.journal attribute as sub-expressions in any complex query.
# For example: search for (MNRAS papers in 2019) or (ApJ papers in 2018)
docs = Document.select()\
               .where(
                   ((Document.journal.abbreviation == "MNRAS") & (Document.year == 2019))
                   | ((Document.journal == apj) & (Document.year == 2018))
               )
```


## The `Document.journal` attribute

The {obj}`ads.Document.journal` field does not exist on the ADS server. You can't search for it,
and it's not an attribute that is returned by the ADS server. It is a special foreign key field 
of the {obj}`ads.Document` data model.

The `ads` package request the {obj}`ads.Document.bibcode` from ADS with every search, parses 
the journal's bibliographic abbreviation from the bibcode, and returns an {class}`ads.Journal` object. 
When searching for documents, any expression referencing {class}`ads.Journal` is resolved into a search filter on {obj}`ads.Document.bibstem`. That allows us to access the {obj}`ads.Document.journal` attribute, and to create expressions using that attribute. 

That's why you won't find the `journal` field on the [NASA ADS API documentation](http://adsabs.github.io/help/api/api-docs.html),
or on the [comphrensive list of operators](https://ui.adsabs.harvard.edu/help/search/comprehensive-solr-term-list).


```{admonition} Contributions
:class: note

Simon J. Murphy (University of Sydney) [first proposed](https://github.com/andycasey/ads/issues/111)  the idea of accessing the interpreted journal name as an attribute of {class}`ads.Document`.
```