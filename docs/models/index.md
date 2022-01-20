---
hide-toc: true
---

# Data models

Most ADS users only ever use the document search service, and usually through the browser. This service uses [Apache Solr](https://solr.apache.org/), a flexible search engine that allows for fast document searches. However, the ADS has many other **awesome** services, including [libraries](https://ui.adsabs.harvard.edu/help/libraries/), curating [journals](https://adsabs.harvard.edu/abs_doc/journals.html) and [affiliations](https://ui.adsabs.harvard.edu/blog/affils-update), providing [custom notifications](http://adsabs.github.io/help/userpreferences/myads), or [visualisations](http://adsabs.github.io/help/actions/visualize), and more. But those services do not use Apache Solr (and nor should they): each service has different API endpoints, and the way to access those services is necessarily different. 

When updating this `ads` Python package I wanted to provide a consistent interface to access all these services, so users could get the most out of ADS. For this reason, Version 1 of the `ads` package uses data models and [object relational mapping](https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping) (ORM) to interface with the ADS API. 

This approach has a number of benefits:
- Access all field names using tab completion, so you don't have to remember them! 
- Allows for complex queries that are not possible with a single ADS search.
- Provides a consistent interface to retrieve documents, libraries, journals, affiliations, or notifications ({obj}`ads.Document`, {obj}`ads.Library`, {obj}`ads.Journal`, {obj}`ads.Affiliation`, or {obj}`ads.Notification`).
- These data models also know how to relate to each other, giving richer search functionality (e.g., search by country of affiliation).
- Use Python logic to construct queries without needing to know the Apache Solr syntax. For example:
  - *"Was it 'year:()' or 'year:[]' I needed?"*
  - *"How do I do exact string matching?"*
  - *"How do I search by name for the third author?"*
    
If you haven't used data models or an ORM before then you might get the feeling that it seems a little *magical*. Don't worry: this documentation provides lots of examples to do what you need. 

```{admonition} A tip if you're *old-school* and don't like change!
:class: tip
If you already have hand-crafted Solr queries that you want to supply directly to ADS, you can still do that using the {obj}`ads.SearchQuery` interface.
See [this tutorial on providing explicit Solr queries](#).
```

## Contents

```{toctree}
document
journal
affiliation
library
```
