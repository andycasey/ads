**A Python Module to Interact with NASA's ADS that Doesn't Suck™**
==================================================================

[![Build Status](http://img.shields.io/travis/andycasey/ads.svg?branch-master)](https://travis-ci.org/andycasey/ads) [![PyPi download count image](http://img.shields.io/pypi/dm/ads.svg)](https://pypi.python.org/pypi/ads/)

If you're in research, then you pretty much _need_ NASA's ADS. It's tried, true, and people go crazy on the rare occasions when it goes down.

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

**Rate limits & optimising your code**

The ADS uses rate limits to ensure that people cannot abuse the API, but this can be pretty annoying if you get locked out when trying to build an application. To avoid such scenarios, there are a few tools to help you. First, you may want to see what your remaining limits are for different end points:

```python
>>> q = ads.SearchQuery(q='star')
>>> for paper in q:
>>>     print paper.title, paper.citation_count
...
>>> q.get_ratelimits()
>>> {'limit': '5000', 'remaining': '4899', 'reset': '1459987200'}
```

This tells us our remaining limit for the `/search` end point is 4899, which will be reset to 5000 after a 24 hour period. Each `Query` object has this method. If you want to see all of your rates for your session, you can do that also:

```python
>>> from ads.utils import get_ratelimits
>>> get_ratelimits()
>>> {'/export': {'limit': None, 'remaining': None, 'reset': None},
 '/metrics': {'limit': None, 'remaining': None, 'reset': None},
 '/search': {'limit': '5000', 'remaining': '4899', 'reset': '1459987200'}}
```

You can see the request didn't contact the other end points and so they have `None` entries. If you want to see how many requests were made for your specific query, and to which end points, you can do:

```python
>>> q.get_request_stats()
>>> {'/search': {'requests': 51, 'test_requests': 0}}
```

At this stage it should be clear that you don't need 51 requests to print the `title` and `citation_count` for the documents you requested. The problem is that `citation_count` is not included in the requested fields, and so each article is lazy loading `citation_count` on demand, which requires an extra contact to the API. 1 request for the intial set of documents, 50 more for each `citation_count` (50 documents are returned as the default requested is `rows=50`). You can request this field upfront, and check the requests:

```python
>>> q = ads.SearchQuery(q='star', fl=['title', 'citation_count'])
...
>>> q.get_request_stats()
>>> {'/search': {'requests': 1, 'test_requests': 0}}
```

Maybe you don't want to waste your rate limit at all when prototyping your application. This is also feasible by setting the `test` attribute:
```python
>>> q = ads.SearchQuery(q='star', test=True)
>>> p = list(q)
>>> q.get_request_stats()
>>> {'/search': {'requests': 0, 'test_requests': 1}}
>>> q.get_ratelimits()
>>> {'limit': '400', 'remaining': '399', 'reset': '1436313600'}
```
You now can see that your query would have made 1 request to the API, but instead it received fake stub data. This is exceedingly useful for end points that you could accidentally use your quota without knowing beforehand:
```python
>>> q = ads.SearchQuery(q='star', test=True, rows=100)
>>> for paper in q:
>>>     print paper.bibtex
...
>>> q.get_request_stats()
>>> {'/export': {'requests': 0, 'test_requests': 100},
 '/search': {'requests': 0, 'test_requests': 1}}
```

It just so happens that the export end point rate limit is 100, and so you would have been blocked for 24 hours if you ran the above code on the live service. You can avoid the above repeat requests to `/export` by sending all the bibcodes:
```python
>>> q = ads.SearchQuery(q='star', rows=100)
>>> bibcodes = [paper.bibcode for paper in q]
>>> e = ads.ExportQuery(bibcodes=bibcodes)
>>> bibtex = e.execute()
>>> print bibtex
>>> @ARTICLE{2013A&A...552A.143S,
   author
...
>>> q.get_request_stats()
>>> {'/search': {'requests': 1, 'test_requests': 0}}

>>> e.get_request_stats()
>>> {'/export': {'requests': 1, 'test_requests': 0}}

>>> get_ratelimits()
>>> {'/export': {'limit': '100', 'remaining': '99', 'reset': '1459987200'},
 '/metrics': {'limit': None, 'remaining': None, 'reset': None},
 '/search': {'limit': '5000', 'remaining': '4999', 'reset': '1459987200'}}
```



**Authors**

Vladimir Sudilovsky & Andy Casey, Geert Barentsen, Dan Foreman-Mackey, Miguel de Val-Borro

**License**

Copyright 2014 the authors 

This is open source software available under the MIT License. For details see the LICENSE file.
