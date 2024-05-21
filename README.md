# A Python Module to Interact with NASA's ADS that Doesn't Suck™

If you're in astro research, then you pretty much *need* NASA's ADS. It's tried, true, and people go crazy on the rare occasions when it goes down.

* Docs: https://ads.readthedocs.io/
* Repo: https://github.com/andycasey/ads
* PyPI: https://pypi.python.org/pypi/ads

[![Build Status](https://travis-ci.org/andycasey/ads.svg?branch=master)](https://travis-ci.org/andycasey/ads)
[![Coverage Status](https://coveralls.io/repos/github/andycasey/ads/badge.svg?branch=master)](https://coveralls.io/github/andycasey/ads?branch=master)

## Quickstart

```python
import ads
ads.config.token = 'secret token'

papers = ads.SearchQuery(q="supernova", sort="citation_count")
for paper in papers:
    print(paper.title[0])
```

You can expect to see some titles like this:
```
Maps of Dust Infrared Emission for Use in Estimation of Reddening and Cosmic Microwave Background Radiation Foregrounds
Measurements of Omega and Lambda from 42 High-Redshift Supernovae
Observational Evidence from Supernovae for an Accelerating Universe and a Cosmological Constant
First-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Determination of Cosmological Parameters
Abundances of the elements: Meteoritic and solar
```

## Running tests

```bash
cd /path/to/ads
pip install -e . "ads[tests]"
python -m unittest discover
```
