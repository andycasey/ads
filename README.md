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
````
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
````
>>> people = list(ads.SearchQuery(first_author="Reiss, A"))

>>> people[0].author
[u'Reiss, A. W.']
````

Or papers where they are anywhere in the author list:
````
>>> papers = list(ads.SearchQuery(author="Reiss, A"))

>>> papers[0].author
[u'Goodwin, F. E.', u'Henderson, D. M.', u'Reiss, A.', u'Wilkerson, John L.']
````

Or search by affiliation:
````
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

````
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

**Authors**

Vladimir Sudilovsky & Andy Casey, Geert Barentsen, Dan Foreman-Mackey, Miguel de Val-Borro

**License**

Copyright 2014 the authors 

This is open source software available under the MIT License. For details see the LICENSE file.
