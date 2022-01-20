---
hide-toc: true
---

# Miscellaneous 

The {obj}`ads.services.misc` namespace is for exposing miscellaneous services offered by ADS. These are services that have only a single API end point.

## Citation helper

Given a set of documents, this service uses a 'friends of friends' analysis to suggest up to ten missing citations. These missing citations cite and/or are cited by the given documents, but are not included in the list.

For example, [this public library](https://ui.adsabs.harvard.edu/public-libraries/7vKRL51sSFKXUfFVMZHC6g) contains 47 papers from Gaia data releases. Let's use the citation helper to suggest missing citations. Note below that by default the {obj}`ads.services.misc.citation_helper` returns a `ModelSelect` object, which you can use to further filter, order, or sort.

```python
from ads import Document, Library
from ads.services.misc import citation_helper

gaia_library = Library.get(id="7vKRL51sSFKXUfFVMZHC6g")

for suggestion in citation_helper(gaia_library).order_by(Document.year.asc()):
    print(f"# {suggestion.bibcode} {suggestion.title[0]}")

# 1997ESASP1200.....E The HIPPARCOS and TYCHO catalogues. Astrometric and photometric star catalogues derived from the ESA HIPPARCOS Space Astrometry Mission
# 2000A&A...355L..27H The Tycho-2 catalogue of the 2.5 million brightest stars
# 2005ASPC..347...29T TOPCAT &amp; STIL: Starlink Table/VOTable Processing Software
# 2010A&A...523A..48J Gaia broad band photometry
# 2016A&A...595A...1G The Gaia mission
# 2019A&A...628A..94A Photo-astrometric distances, extinctions, and astrophysical parameters for Gaia DR2 stars brighter than G = 18
# 2020AdSpR..65....1P Gaia: The Galaxy in six (and more) dimensions
# 2020svos.conf...11E Gaia's revolution in stellar variability
# 2020MNRAS.497.4246B Completeness of the Gaia verse II: what are the odds that a star is missing from Gaia DR2?
# 2021ARA&A..59...59B Microarcsecond Astrometry: Science Highlights from Gaia
```

