**A Python Module to Interact with NASA's ADS that Doesn't Suck™**
==================================================================

[![Build Status](https://travis-ci.org/andycasey/ads.png?branch=master)](https://travis-ci.org/andycasey/ads) [![PyPi download count image](https://pypip.in/d/ads/badge.png)](https://pypi.python.org/pypi/ads/)

If you're in research, then you pretty much _need_ NASA's ADS. It's tried, true, and people go crazy on the rare occasions when it goes down.

**Getting Started**

1. You'll need an API key from NASA ADS labs. Sign up for the newest version of ADS search [here](http://labs.adsabs.harvard.edu/adsabs/user/signup), then you can apply for API access by filling out [this form](https://docs.google.com/spreadsheet/viewform?formkey=dFJZbHp1WERWU3hQVVJnZFJjbE05SGc6MQ#gid=0).

2. When you get your API key, save it to a file called ``~/.ads/dev_key`` or save it as an environment variable named ``ADS_DEV_KEY``

3. From a terminal type ``pip install ads`` (or [if you must](https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install), use ``easy_install ads``)

Happy Hacking!


**Examples**

You can use this module to search for some popular supernova papers:
````
In [1]: import ads

In [2]: papers = ads.query("supernova", sort="citations", rows=5)

In [3]: for paper in papers:
    print(paper.title)
   ...:     
[u'Maps of Dust Infrared Emission for Use in Estimation of Reddening and Cosmic Microwave Background Radiation Foregrounds']
[u'Measurements of Omega and Lambda from 42 High-Redshift Supernovae']
[u'Observational Evidence from Supernovae for an Accelerating Universe and a Cosmological Constant']
[u'First-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Determination of Cosmological Parameters']
[u'Abundances of the elements: Meteoritic and solar']
````

Or search for papers first-authored by someone:
````
In [4]: people = list(ads.query(authors="^Reiss, A"))

In [5]: people[0].author
Out[5]: [u'Reiss, A. E.', u'Marchis, F.', u'Emery, J. P.']
````

Or papers where they are anywhere in the author list:
````
In [6]: papers = list(ads.query(authors="Reiss, A"))

In [7]: papers[0].author
Out[7]: 
[u'Freeman, William',
 u'Bishop, J.',
 u'Marchis, F.',
 u'Emery, J.',
 u'Reiss, A. E.',
 u'Hiroi, T.',
 u'Navascu\xe9s, D. Barrado y.',
 u'Shaddad, M. H.',
 u'Jenniskens, P.']
````

Or search by affiliation:
````
In [8]: papers = list(ads.query(affiliation="*stromlo*", rows=5))

In [8]: papers[0].aff
Out[8]: 
[u'Institute of Astronomy, University of Cambridge, Madingley Road, Cambridge CB3 0HA, UK;',
 u'Astronomisches Rechen-Institut, Zentrum f\xfcr Astronomie der Universit\xe4t Heidelberg, D-69120 Heidelberg, Germany',
 u'JHU-APL, 11100 Johns Hopkins Road, Laurel, MD 20723, USA',
 u"UJF-Grenoble 1/CNRS-INSU, Institut de Plan\xe9tologie et d'Astrophysique (IPAG) UMR 5274, F-38041 Grenoble, France; Laboratorio Franco-Chileno de Astronomia (UMI 3386: CNRS - U de Chile/PUC/U Conception), Santiago, Chile",
 u'Department of Physics, University of Cincinnati, Cincinnati, OH 45221-0011, USA',
 u'Institute of Astronomy, University of Cambridge, Madingley Road, Cambridge CB3 0HA, UK',
 u'Research School of Astronomy and Astrophysics, The Australian National University, Mount Stromlo Observatory, Cotter Road, Weston Creek, ACT 2611, Australia',
 u'Department of Earth, Atmospheric and Planetary Sciences, Massachusetts Institute of Technology, 77 Massachusetts Avenue, Cambridge, MA 02139, USA',
 u'The Aerospace Corporation, Mail Stop: M2-266, P.O. Box 92957, Los Angeles, CA 90009-2957, USA',
 u'The Aerospace Corporation, Mail Stop: M2-266, P.O. Box 92957, Los Angeles, CA 90009-2957, USA',
 u'The Aerospace Corporation, Mail Stop: M2-266, P.O. Box 92957, Los Angeles, CA 90009-2957, USA',
 u'The Aerospace Corporation, Mail Stop: M2-266, P.O. Box 92957, Los Angeles, CA 90009-2957, USA',
 u'SRON Netherlands Institute for Space Research, NL-9747 AD Groningen, the Netherlands',
 u'The Boeing Company, 535 Lipoa Pkwy, Kihei, HI 96753, USA',
 u'Research School of Astronomy and Astrophysics, The Australian National University, Mount Stromlo Observatory, Cotter Road, Weston Creek, ACT 2611, Australia']
````

In the above examples we ````list()```` the results from ````ads.query```` because ````ads.query```` is a generator, allowing us to return any number of papers for a given query. It will parallelise threads and continue to retrieve papers relevant to your query. Each object returned is an ````ads.Article```` object, which has a number of *very* handy attributes:

````
In [9]: first_paper = papers[0]

In [10]: first_paper
Out[10]: <ads.Article object at 0x1036b3b90>

# Show some brief details about the paper
In [11]: print first_paper
<Kennedy et al. 2014, 2014MNRAS.438.3299K>

# You can access attributes of an object in IPython by using the 'tab' button:
In [12]: first_paper.
first_paper.abstract              first_paper.bibtex                first_paper.database              first_paper.keyword               first_paper.property              first_paper.title                 
first_paper.aff                   first_paper.build_citation_tree   first_paper.doi                   first_paper.keyword_norm          first_paper.pub                   first_paper.url                   
first_paper.author                first_paper.build_reference_tree  first_paper.id                    first_paper.keyword_schema        first_paper.pubdate               first_paper.volume                
first_paper.bibcode               first_paper.citation_count        first_paper.identifier            first_paper.metrics               first_paper.reference_count       first_paper.year                  
first_paper.bibstem               first_paper.citations             first_paper.issue                 first_paper.page                  first_paper.references            
````

Which allows you to easily build complicated queries. A short list of [more advanced examples](https://github.com/andycasey/ads/tree/master/examples) are included, and there are more to come. Feel free to fork this repository and add your own examples!

**Contributors**
Dan Foreman-Mackey
Miguel de Val-Borro

**License**

Copyright 2014 Andy Casey and contributors

This is open source software available under the MIT License. For details see the LICENSE file.
