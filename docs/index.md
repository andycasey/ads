---
hide-toc: true
---

::::{grid}
:reverse:
:gutter: 2 1 1 1
:margin: 4 4 1 1

:::{grid-item}
:columns: 4

```{image} ./_static/ads-logo-square.svg
:width: 100px
```
:::

:::{grid-item}
:columns: 8
:class: sd-fs-3

A Python client for the SAO/NASA Astrophysics Data System
:::

::::
**[Asynchronous coroutines for faster queries](https://google.com)**
: Now you can make queries synchronously with improved pagination, or search ten times faster using asynchronous coroutines.

**[A fast command line tool](reference/notebooks)**
: Query for references or documents at lightening speed from a terminal.

**[Update remote ADS libraries with ease](launch)**
: Use a Pythonic API to create, update, and delete remote libraries.

**[Make sophisticated metrics queries](https://getbootstrap.com/docs/4.0/getting-started/introduction/)**
: New querying tools for building complex metrics queries and visualizations.

:::{seealso}
``ads`` 1.0 is only compatible with Python 3.x. If you haven't already upgraded from Python 2, two years ago was the time.
:::


&nbsp;

&nbsp;

&nbsp;


``ads`` is a Python package for interacting with the Astrophysics Data System (ADS), a digital library portal for researchers in astronomy and physics, 
operated by the [Smithsonian Astrophysical Observatory](https://www.cfa.harvard.edu/sao) (SAO) under a [NASA](https://nasa.gov) grant.


What's new?
----------

- Asynchronous coroutines to speed up queries by an order of magnitude
- A fast command line tool for retrieving documents
- Create and update remote ADS libraries with ease
- More sophisticated metrics queries
- ...
- Automatic request throttling to avoid overloading NASA/ADS services



# Furo

A clean customisable Sphinx documentation theme.

```{include} ../README.md
:start-after: <!-- start elevator-pitch -->
:end-before: <!-- end elevator-pitch -->
```

```{toctree}
:hidden:

quickstart
customisation/index
reference/index
recommendations
```

```{toctree}
:caption: Development
:hidden:

contributing/index
kitchen-sink/index
stability
changelog
license
GitHub Repository <https://github.com/pradyunsg/furo>
```