---
hide-toc: true
---

```{toctree}
:caption: Setup
:hidden:

install
api-key
```

```{toctree}
:caption: User guide
:hidden:
:maxdepth: 1

getting-started/index
services/index
tutorials/index
api
rate-limits
```

```{toctree}
:caption: Developer guide
:hidden:

motivation
upgrading
limitations
```

```{toctree}
:caption: External links
:hidden:

SAO/NASA ADS API documentation <http://adsabs.github.io/help/api/apidocs.html>
mirrors
GitHub repository <https://github.com/andycasey/ads>
```


::::{grid}
:reverse:
:gutter: 2 1 1 1
:margin: 4 4 1 1

:::{grid-item}
:columns: 4

```{image} ./_static/ads-logo-square.png
:width: 100px
```
:::

:::{grid-item}
:columns: 8
:class: sd-fs-3

A Python client for the SAO/NASA Astrophysics Data System
:::

::::
**[Use object relational mappers for complex, easy-to-read queries](#)**
: New data models for building programmatic queries.

**[New ways to search](#)**
: Search by author email, journal title, country of affiliation, and more.

**[Asynchronous queries for faster results](#)**
: Use asynchronous coroutines for blazingly fast queries, or make synchronous queries with improved pagination behaviour.

**[Libraries and notifications](#)**
: Use a Pythonic API to create, update, and delete remote libraries or myADS notifications.

**And much more...**
: There's a lot of changes in version 1 of the ``ads`` module. Explore these docs to learn more.

```{important} Important
:class: important
Version 1.0 of ``ads`` is only compatible with Python 3. If you haven't upgraded from Python 2, the time to upgrade was [two years ago](https://www.python.org/doc/sunset-python-2/).
```


&nbsp;


``ads`` is a community-built Python package for interacting with the Astrophysics Data System (ADS). ADS is a digital library portal for researchers in astronomy and physics, which is operated by the [Smithsonian Astrophysical Observatory](https://www.cfa.harvard.edu/sao) (SAO) under a [NASA](https://nasa.gov) grant. The SAO/NASA ADS logo shown above is authored and owned by SAO/NASA ADS, and is [displayed under a Creative Commons License with Attribution](https://ui.adsabs.harvard.edu/help/logos/).

&nbsp;


