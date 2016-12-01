**A Python Module to Interact with NASA's ADS that Doesn't Suck™**
==================================================================

[![Build Status](http://img.shields.io/travis/andycasey/ads.svg?branch-master)](https://travis-ci.org/andycasey/ads) [![Coverage Status](https://coveralls.io/repos/github/andycasey/ads/badge.svg?branch=master)](https://coveralls.io/github/andycasey/ads?branch=master) [![PyPi download count image](http://img.shields.io/pypi/dm/ads.svg)](https://pypi.python.org/pypi/ads/)

If you're in astro research, then you pretty much _need_ NASA's ADS. It's tried, true, and people go crazy on the rare occasions when it goes down.

**Getting Started**

1. You'll need an API key from NASA ADS labs. Sign up for the newest version of ADS search at https://ui.adsabs.harvard.edu, visit account settings and generate a new API token. The official documentation is available at https://github.com/adsabs/adsabs-dev-api

2. When you get your API key, save it to a file called ``~/.ads/dev_key`` or save it as an environment variable named ``ADS_DEV_KEY``

3. From a terminal type ``pip install ads`` (or [if you must](https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install), use ``easy_install ads``)

Happy Hacking!


**Examples**

You can use this module to search for some popular supernova papers:
````python
>>> import ads

# Opps, I forgot to follow step 2 in "Getting Started"
>>> ads.config.token = 'my token'

>>> papers = ads.SearchQuery(q="supernova", sort="citation_count")

>>> for paper in papers:
>>>    print(paper.title)
   ...:
[u'Maps of Dust Infrared Emission for Use in Estimation of Reddening and Cosmic Microwave Background Radiation Foregrounds']
[u'Measurements of Omega and Lambda from 42 High-Redshift Supernovae']
[u'Observational Evidence from Supernovae for an Accelerating Universe and a Cosmological Constant']
[u'First-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Determination of Cosmological Parameters']
[u'Abundances of the elements: Meteoritic and solar']
````

Or search for papers first-authored by someone:
````python
>>> people = list(ads.SearchQuery(first_author="Reiss, A"))

>>> people[0].author
[u'Reiss, A. W.']
````

Or papers where they are anywhere in the author list:
````python
>>> papers = list(ads.SearchQuery(author="Reiss, A"))

>>> papers[0].author
[u'Goodwin, F. E.', u'Henderson, D. M.', u'Reiss, A.', u'Wilkerson, John L.']
````

Or search by affiliation:
````python
>>> papers = list(ads.SearchQuery(aff="*stromlo*"))

>>> papers[0].aff
[u'University of California, Berkeley',
 u'University of Kansas',
 u'Royal Greenwich Observatory',
 u"Queen's University",
 u'Mt. Stromlo Observatory',
 u'University of Durham']
````

In the above examples we `list()` the results from `ads.SearchQuery` because `ads.SearchQuery` is a generator, allowing us to return any number of articles. 
To prevent deep pagination of results, a default of `max_pages=3` is set. 
Feel free to change this, but be aware that each new page fetched will count against your daily API limit. 
Each object returned is an ````ads.Article```` object, which has a number of *very* handy attributes and functions:

````python
>>> first_paper = papers[0]

>>> first_paper
<ads.search.Article at 0x7ff1b913dd10>

# Show some brief details about the paper
>>> print first_paper
<Zepf, S. et al. 1994, 1994AAS...185.7506Z>

# You can access attributes of an object in IPython by using the 'tab' button:
>>> first_paper.
first_paper.abstract              first_paper.build_citation_tree   first_paper.first_author_norm     first_paper.keys                  first_paper.pubdate
first_paper.aff                   first_paper.build_reference_tree  first_paper.id                    first_paper.keyword               first_paper.read_count
first_paper.author                first_paper.citation              first_paper.identifier            first_paper.metrics               first_paper.reference
first_paper.bibcode               first_paper.citation_count        first_paper.issue                 first_paper.page                  first_paper.title
first_paper.bibstem               first_paper.database              first_paper.items                 first_paper.property              first_paper.volume
first_paper.bibtex                first_paper.first_author          first_paper.iteritems             first_paper.pub                   first_paper.year
````

Which allows you to easily build complicated queries. Feel free to fork this repository and add your own examples!

**Rate limits and optimisations**

*Sandbox*

The ADS's API uses rate limits to ensure that people cannot abuse it, but this can be pretty annoying if you get locked out when trying to build an application. To avoid such scenarios, you can use the ADS sandbox environment when prototyping:

```python
>>> import ads.sandbox as ads
>>> q = ads.SearchQuery(q='star')
>>> for paper in q:
>>>     print paper.title, paper.citation_count
```

This will not access the live API, but provide mocked responses. When you're ready to go live with your code, simply change the import line to:
```python
>>> import ads
```

and you're ready to go.

*Rate limit usage*

There are helpers that let you keep track of your rate limit, so you can also see how many requests your application is making to the API:

```python
>>> import ads
>>> q = ads.SearchQuery(q='star')
>>> for paper in q:
>>>     print paper.title, paper.citation_count
>>> ....
>>>
>>> q.response.get_ratelimits()
>>> {'limit': '5000', 'remaining': '4899', 'reset': '1459987200'}
```

or

```python
>>> import ads
>>> r = ads.RateLimits('SearchQuery')
>>> q = ads.SearchQuery(q='star')
>>> for paper in q:
>>>     print paper.title, paper.citation_count
>>> ....
>>>
>>> r.get_info()
>>> {'SearchQuery': {'limit': '5000', 'remaining': '4899', 'reset': '1459987200'}}
```

If you prefer to use your own mocking package, or mock your responses manually, you can access both the stubdata and HTTPretty mocks from the package:
```python
>>> import ads
>>> from ads.tests import mocks
>>>
>>> q = ads.SearchQuery(q='star')
>>> with mocks.MockSolrResponse(ads.SEARCH_URL):
>>>     q.execute()
>>> print q.articles[0].title
....
```

and
```python
>>> from ads.tests.stubdata import solr
>>> print(solr.example_solr_response)
....
>>>         "title":["Dusty Mg II Absorbers: Implications for the Gamma-ray Burst/Quasar Incidence Discrepancy"],
        "page":["56"],
        "_version_":1505343681984462848,
        "indexstamp":"2015-06-29T19:53:26.54Z"}]
  }}
>>>
  ```

*Lazy loading of attributes*

One thing to be aware of when making queries is the use of lazy loading. This feature is great when prototyping some code, but can hurt you when in production. In the following example, `citation_count` is requested (for each paper) from the ADS API because it was not returned on the first request


```python
>>> import ads
>>> q = ads.SearchQuery(q='star')
>>> for paper in q:
>>>     print paper.title, paper.citation_count
>>> ....
```

This would result in `N=1+number_of_docs` requests rather than `N=1`. To ensure it is `N=1` you can request the field ahead of time:

```python
>>> import ads
>>> q = ads.SearchQuery(q='star', fl=['id', 'bibcode', 'title', 'citation_count'])
>>> for paper in q:
>>>     print paper.title, paper.citation_count
>>> ....
```

**Authors**

Vladimir Sudilovsky & Andy Casey, Geert Barentsen, Dan Foreman-Mackey, Miguel de Val-Borro, and Jonny Elliott

**License**

Copyright 2016 the authors

This is open source software available under the MIT License. For details see the LICENSE file.
