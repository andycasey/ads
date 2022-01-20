# Documents


## The {obj}`ads.Document` object

The {obj}`ads.Document` object is used to represent a record in ADS. We use this data model and an [object-relational mapper](https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping) (ORM) to search and filter for documents on ADS in a programmatic way. In other words, you can write expressions like `(Document.year < 2020) & Document.title.like("JWST")` and have them translated into a Solr search query.

Let's get started with a quick example where we just select one document. If you only want one document, then use the {func}`ads.Document.get()` function. If you want possibly more than one document, use the {func}`ads.Document.select()` method. In the first tab of the example below you can see the executable Python code, and in the second tab you can see the output.

``````{tab} Python
```python
from ads import Document

# Retrieve a single document from ADS
doc = Document.get(bibcode="2020MNRAS.498.1420W")
print(doc)

# Let's print some information about this document.
print(f"Title: {doc.title[0]}")
print(f"   By: {'; '.join(doc.author)}")
```
``````
``````{tab} Output
```
<Document: bibcode=2020MNRAS.498.1420W>
Title: H0LiCOW - XIII. A 2.4 per cent measurement of H<SUB>0</SUB> from lensed quasars: 5.3σ tension between early- and late-Universe probes
   By: Wong, Kenneth C.; Suyu, Sherry H.; Chen, Geoff C. -F.; Rusu, Cristian E.; Millon, Martin; Sluse, Dominique; Bonvin, Vivien; Fassnacht, Christopher D.; Taubenberger, Stefan; Auger, Matthew W.; Birrer, Simon; Chan, James H. H.; Courbin, Frederic; Hilbert, Stefan; Tihhonova, Olga; Treu, Tommaso; Agnello, Adriano; Ding, Xuheng; Jee, Inh; Komatsu, Eiichiro; Shajib, Anowar J.; Sonnenfeld, Alessandro; Blandford, Roger D.; Koopmans, Léon V. E.; Marshall, Philip J.; Meylan, Georges
```
``````

If we want to select multiple documents, we use the {func}`ads.Document.select()` function. We will get into more complex queries later, but here is a basic example:

``````{tab} Python
```python
from ads import Document

# Classic bangerz
docs = Document.select().where(Document.year < 1505)
for doc in docs:
    print(f"'{doc.title[0]}' by {'; '.join(doc.author)} ({doc})")
```
``````
``````{tab} Output
```
'Ad illustrissimum D. Io. Bentivolum Dominici Marie Ferrarensis de Novaria Pronosticon in annum domini M.D.IIII' by Novara, Dominico Maria (<Document: bibcode=1503aidi.book.....N>)
'Apologia eiusdem in librum suum de sole; &amp; lumine.' by Ficino, Marsilio (<Document: bibcode=1503aels.book.....F>)
'D scientia motvs orbis.' by Masha'Allah; Gerardus, Cremonensis (<Document: bibcode=1504dsmo.book.....M>)
'Tabule astronomice Elisabeth Regine' by Alfonsus (<Document: bibcode=1503taer.book.....A>)
```
``````

The


## Document fields


The {obj}`ads.Document` data model has some attributes that are viewable (e.g., {obj}`ads.Document.title`), some that are searchable but not viewable (e.g., {obj}`ads.`)


### Search-only fields

### Data model notes

-> tutorials on searching by author, first author, title, exact name match, etc.

## Basic document searches

### Single document

### Multiple documents

- modelselect not executed until iterate over

### Filtering

### Ordering

### Limits

## Advanced document searches

### With {obj}`ads.Journal`

### With {obj}`ads.Affiliation`

### With {obj}`ads.Library`

## BigQuery
## Use explicit Solr queries

