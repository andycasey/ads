# Affiliations

On [15 January 2020](https://ui.adsabs.harvard.edu/blog/affiliations-feature) the ADS team publicly announced an affiliations feature that described how a curated list of institutional affiliations is built and maintained, and how it can be incorporated into literature searches. A follow-up blog post on [15 Apr 2021](https://ui.adsabs.harvard.edu/blog/affils-update) describes the progress to this feature.

There is good motivation for this feature. The affiliation strings of documents in ADS frequently include typographical errors (as provided by users), or users will refer to the same institution with a very different affiliation string. A single institution might have dozens of variations of affiliation strings that appear regularly.

The `ads` Python package uses the affiliation identifiers (`aff_id`) introduced in the two blog posts linked above, and includes a data model {class}`ads.Affiliation`. When a document is returned by ADS, any affiliation identifiers are represented in the {obj}`ads.Document.affiliation` attribute as {class}`ads.Affiliation` objects. This allows for complex search queries using affiliations, countries, and relationships between affiliations.

You will need the following imports in order to execute all code blocks on this page:
```python
from ads import Affiliation, Document
from ads.utils import flatten
```

## The `Affiliation` data model

The {class}`ads.Affiliation` data model contains the following fields:

- {obj}`ads.Affiliation.id`: the unique (child) identifier for the affiliation
- {obj}`ads.Affiliation.parent`: a foreign key field to any parent identifiers for this affiliation
- {obj}`ads.Affiliation.abbreviation`: the abbreviated affiliation name (e.g., 'MIT')
- {obj}`ads.Affiliation.canonical_name`: the full affiliation name
- {obj}`ads.Affiliation.country`: the name of the country that the affiliation is located in

## Selecting affiliations

You can select a single `Affiliation` object with the {func}`ads.Affiliation.get` method, or select multiple records using the {func}`ads.Affiliation.select` method. Here are a few examples:

```python
# Retrieve a single affiliation based on an exact expression.
mit = Affiliation.get(abbreviation="MIT")

# Get a single affiliation, but we don't care which one.
affiliation = Affiliation.get()

# Select 10 affiliations with "observatory" (case-insensitive) in the name,
# ordered by canonical name.
observatories = Affiliation.select()\
                           .where(Affiliation.canonical_name.contains("observatory"))\
                           .order_by(Affiliation.canonical_name.asc())\
                           .limit(10)
for observatory in observatories:
    print(f"> {observatory.id} {observatory.canonical_name} ({observatory.abbreviation})")
> A11178 AK Volcano Observatory, Fairbanks (AVO)
> A05329 Aalto University, Metsahovi Radio Observatory (Metsahovi Rad Obs)
> A05229 Abastumani Astrophysical Observatory (Abast Ast Obs)
> A05229 Abastumani Astrophysical Observatory (Abast Ast Obs)
> A11178 Alaska Volcano Observatory, Fairbanks (AVO)
> A11489 Archenhold Observatory, Berlin, Germany (Archenhold Obs)
> A01804 Arecibo Observatory (Arecibo)
> A01804 Arecibo Observatory (Arecibo)
> A01804 Arecibo Observatory (Arecibo)
> A11739 Armagh Observatory, Ireland (Armagh Obs)
```

Here we can see a few repeated records: 
- two for the Abastumani Astrophysical Observatory (Abast Ast Obs), 
- two for the Alaska Volcano Observatory (AVO), with slightly different names, and
- three for Arecibo Observatory.

The reason that we received multiple records for the same affiliation is because some affiliations have child/parent relationships to other affiliations.

## Parent and child affiliation references

Some affiliations have relationships to other affiliations. Currently, ADS only supports parent/child references between affiliations. An example might be departments (children) within a university (parent), where both the department and the university have their own recognised affiliation identifier. Another example might be a research organisation that is spread across geographical areas:

```python
# The Center for Excellence for All Sky Astrophysics (CAASTRO)
# was an Australian Research Council-funded project that included 
# research institutions across Australia, and elsewhere.
caastro = Affiliation.get(abbreviation="CAASTRO")
print(f"# {caastro.id}: {caastro.abbreviation} - {caastro.canonical_name}")
# A11661: CAASTRO - Center for Excellence for All Sky Astrophysics

parent = caastro.parent
print(f"# Parent: {parent.id}: {parent.abbreviation} - {parent.canonical_name}")
# Parent: A00172: Curtin U - Curtin University, Australia
```

In many cases there is only a single parent reference. But in this case we know that there are multiple records for CAASTRO, because it is a child reference of multiple parent (universities). We can use the {obj}`ads.Affiliation.parents` property to run a self-join on the {class}`ads.Affiliation` table and find all possible parents of this affiliation.

```python
for parent in caastro.parents:
    print(f"# {parent.id}: {parent.canonical_name}")
# A00172: Curtin University, Australia
# A00254: University of Queensland, Australia
# A00339: Australian National University, Canberra
# A00361: University of Melbourne, Australia
# A00446: University of Western Australia
# A00650: Swinburne University of Technology, Australia
# A00732: University of Sydney, Australia
# A04927: Australian Research Council
```

If we wanted to find all the children referenced by a parent, we can use the {obj}`ads.Affiliation.children` back-reference accessor:

```python
arc = Affiliation.get(canonical_name="Australian Research Council")
for node in arc.children.order_by(Affiliation.canonical_name.asc()):
    print(f"# {node.id}: {node.canonical_name}")
# A11660: Antarctic Climate and Ecosystems Cooperative Research Center
# A11661: Center for Excellence for All Sky Astrophysics
# A11720: Center for Quantum Computation and Communication Technology
# A11705: Center of Excellence for Climate System Science
# A11662: Center of Excellence for Core to Crust Fluid Systems
# A11659: Center of Excellence in Ore Deposits
```

## Using affiliations in search

If you were using the ADS web interface, there are three fields available for searching by affiliation:

- `aff`: Search by the raw affiliation strings provided by authors. This does not use any curated identifiers as part of the search.
- `aff_id`: Search by affiliation identifiers that are parsed and curated by ADS, including synonyms with other institutional system identifiers like GRID or ROR. If you weren't using the `ads` python package, then this would require you to know the [controlled dictionary of institutional identifiers](https://github.com/adsabs/CanonicalAffiliations/blob/master/parent_child.tsv).
- `inst`: This is a shortcut to search for institutions without requiring you to know their parent. The following text is an example from the [ADS blog post](https://ui.adsabs.harvard.edu/blog/affils-update): Unlike `aff_id`, this expands the search to include an institution's children, which is convenient for unique institutions like "CfA". However, for an institution that is not unique, such as "Inst Phy", you will want to include the parent to disambiguate.

In the `ads` package, you can search for documents using any expression that involves {class}`ads.Affiliation` and this expression will be resolved as a search string that filters on `aff_id`. Here are some examples how you could search ADS using the three methods above:

```python
# 1. Search raw affiliation strings for 'Monash'
docs = Document.select()\
               .where(Document.aff.like("Monash"))

# 2. Search curated affiliations for a specific affiliation.
#    We know there will only be one affiliation like 'Flatiron', 
#    but we don't remember the canonical name:
flatiron = Affiliation.get(Affiliation.canonical_name.contains("flatiron"))
#    Note that we want to search 'like' flatiron, so that the Flatiron affiliation
#    can be anywhere among the list of affiliations. We don't want an *exact* match.
docs = Document.select()\
               .where(Document.affiliation.like(flatiron))

# Search by institute field.
docs = Document.select()\
               .where(Document.inst.like("Institute of Physics"))
```

### Search by affiliation name

If you want to search for documents where ADS has identified the affiliation as belonging to one of the curated list of institutional identifiers, but you don't necessarily care about what the affiliation identifier is, you can search by the canonical name or abbreviation of the institute.

For example:
```python
# Search for documents where ADS have parsed MIT from the raw affiliation string
docs = Document.select()\
               .where(Document.affiliation.abbreviation == "MIT")

# Or if you can spell Massachusetts without needing help from Google:
docs = Document.select()\
               .where(Document.affiliation.canonical_name == "Massachusetts Institute of Technology")
```

### Search by country

Some of the affiliations in the curated institutional identifiers have a geographical location. This is expressed only at the country-level, but we can still use this in any complex search query.
 
Let's start with a simple example where we want one document (co-)authored by an Australian.

``````{tab} Right-side-up
```python
doc = Document.get(Document.affiliation.country == "Australia")
# Let's check!
assert any((aff.country == "Australia") for aff in flatten(doc.affiliation))
```
``````
``````{tab} Australians
```python
poɔ = poɔnɯǝuʇ˙ƃǝʇ(poɔnɯǝuʇ˙ɐɟɟᴉlᴉɐʇᴉou˙ɔonuʇɹʎ == ,,∀nsʇɹɐlᴉɐ,,)
```
``````

The expression here, `Document.affiliation.country == "Australia"` is resolved to finding all {class}`ads.Affiliation` records where the country is 'Australia', and then searching ADS with the syntax:
```python
q = "aff_id:(A11664 OR A11678 OR A11680 ... OR A05652 OR A05679)"
```
where `A11664`, `A11678`, `A11680`, etc are all the 146 {obj}`ads.Affiliation.id` values matched by our search on country.

:::{Warning}
The list of curated affiliations is incomplete and biased. Countries will be missing from many curated affiliations. Relationships between parent/child affiliations may be incomplete. You should consider these factors when searching with these fields.
:::