---
hide-toc: false
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
**[Make sophisticated metrics queries](#)**
: New querying tools for building complex metrics queries and visualizations.

**[Asynchronous coroutines for faster queries](#)**
: Use asynchronous coroutines for blazingly fast queries, or make synchronous queries with improved pagination behaviour.

**[Update remote services with ease](#)**
: Use a Pythonic API to create, update, and delete remote libraries or myADS notifications.

**Lots more...**
: There are a lot of new changes in version 1.0 of the ``ads`` module. [See what's new](changelog).

:::{important}
Version 1.0 of ``ads`` is only compatible with Python 3. If you haven't yet upgraded from Python 2, [two years ago](https://www.python.org/doc/sunset-python-2/) was the time to upgrade.
:::


&nbsp;


``ads`` is a community-built Python package for interacting with the Astrophysics Data System (ADS). ADS is a digital library portal for researchers in astronomy and physics, which is operated by the [Smithsonian Astrophysical Observatory](https://www.cfa.harvard.edu/sao) (SAO) under a [NASA](https://nasa.gov) grant.


&nbsp;


# Basic examples

You can search by keywords for documents on ADS.

``````{tab} Synchronous
```python
import ads

for document in ads.SearchQuery(q="stellar astrophysics"):
   print(document.title)
```
``````
``````{tab} Asynchronous
```python
import ads

def main():
   async for document in ads.SearchQuery(q="stellar astrophysics"):
      print(document.title)

asyncio.run(main())
```
``````
``````{tab} Example Output
```
['foo']
```
``````

:::{ToDo}
- Search by author
- Search by year
- Search by affiliation
:::



# Contents

```{toctree}
:caption: Getting started
:hidden:

getting-started/index
```

&nbsp;


```{toctree}
:caption: User Guide
:maxdepth: 2
user/journal
user/affiliations
user/libraries
user/rate-limits
user/export
user/vis
api-docs
```

&nbsp;

```{toctree}
:caption: Tutorials

tutorials/basic
tutorials/async
```

&nbsp; 

```{toctree}
:caption: Development
developer-docs
changelog
```

&nbsp;

```{toctree}
:caption: External links

Search ADS <https://ui.adsabs.harvard.edu/>
SAO/NASA ADS API documentation <http://adsabs.github.io/help/api/api-docs.html>
```

&nbsp; 

```{toctree}
GitHub Repository <https://github.com/andycasey/ads>
```

