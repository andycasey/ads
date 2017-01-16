A Python Module to Interact with NASA's ADS that Doesn't Suck™
==============================================================

If you're in astro research, then you pretty much *need* NASA's ADS.
It's tried, true, and people go crazy on the rare occasions when it goes down.

* Docs: https://ads.readthedocs.io/
* Repo: https://github.com/andycasey/ads
* PyPI: https://pypi.python.org/pypi/ads

.. image:: https://travis-ci.org/andycasey/ads.svg?branch=master
    :target: https://travis-ci.org/andycasey/ads

.. image:: https://coveralls.io/repos/github/andycasey/ads/badge.svg?branch=master
    :target: https://coveralls.io/github/andycasey/ads?branch=master


Quickstart
==========

   >>> import ads
   >>> ads.config.token = 'secret token'
   >>> papers = ads.SearchQuery(q="supernova", sort="citation_count")
   >>> for paper in papers:
   >>>    print(paper.title)
   [u'Maps of Dust Infrared Emission for Use in Estimation of Reddening and Cosmic Microwave Background Radiation Foregrounds']
   [u'Measurements of Omega and Lambda from 42 High-Redshift Supernovae']
   [u'Observational Evidence from Supernovae for an Accelerating Universe and a Cosmological Constant']
   [u'First-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Determination of Cosmological Parameters']
   [u'Abundances of the elements: Meteoritic and solar']