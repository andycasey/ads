# Resolver

The resolver service provides links to external resources associated with a document in ADS. 

There are two API end points for this service:

```{eval-rst}
.. autosummary::
    :nosignatures:

    ads.services.resolver.external_resource
    ads.services.resolver.external_resources
```

In the example below the first tab shows the executable Python code, and the second tab shows the output.

``````{tab} Python
```
import json
from ads import Document
from ads.services.resolver import (external_resource, external_resources)

doc = Document.get(bibcode="2018A&A...616A...1G")

resources = external_resources(doc)

# (Pretty) print all external resources
print(json.dumps(resources, indent=2))
```
``````
``````{tab} Output
```json
[
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "ABSTRACT (1)",
    "url": "/link_gateway/2018A&A...616A...1G/ABSTRACT",
    "type": "abstract",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "CITATIONS (1)",
    "url": "/link_gateway/2018A&A...616A...1G/CITATIONS",
    "type": "citations",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "REFERENCES (1)",
    "url": "/link_gateway/2018A&A...616A...1G/REFERENCES",
    "type": "references",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "COREADS (1)",
    "url": "/link_gateway/2018A&A...616A...1G/COREADS",
    "type": "coreads",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "OPENURL (1)",
    "url": "/link_gateway/2018A&A...616A...1G/OPENURL",
    "type": "openurl",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "GRAPHICS (1)",
    "url": "/link_gateway/2018A&A...616A...1G/GRAPHICS",
    "type": "graphics",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "METRICS (1)",
    "url": "/link_gateway/2018A&A...616A...1G/METRICS",
    "type": "metrics",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "SIMILAR (1)",
    "url": "/link_gateway/2018A&A...616A...1G/SIMILAR",
    "type": "similar",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "ESOURCE (4)",
    "url": "/link_gateway/2018A&A...616A...1G/ESOURCE",
    "type": "esource",
    "count": 4
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "DATA (9)",
    "url": "/link_gateway/2018A&A...616A...1G/DATA",
    "type": "data",
    "count": 9
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "ASSOCIATED (1)",
    "url": "/link_gateway/2018A&A...616A...1G/ASSOCIATED",
    "type": "associated",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "DOI (1)",
    "url": "/link_gateway/2018A&A...616A...1G/DOI",
    "type": "doi",
    "count": 1
  },
  {
    "bibcode": "2018A&A...616A...1G",
    "title": "ARXIV (1)",
    "url": "/link_gateway/2018A&A...616A...1G/ARXIV",
    "type": "arxiv",
    "count": 1
  }
]
```
``````

In the output tab we can see there are four ``ESOURCE``s available. Let's retrieve those specific resources:

``````{tab} Python
```
esource = external_resource(doc, "esource")
print(json.dumps(esource, indent=2))
```
``````
``````{tab} Output
```json
{
  "service": "",
  "action": "display",
  "links": {
    "count": 4,
    "bibcode": "2018A&A...616A...1G",
    "link_type": "ESOURCE",
    "records": [
      {
        "title": "https://arxiv.org/abs/1804.09365",
        "url": "https://arxiv.org/abs/1804.09365",
        "link_type": "ESOURCE|EPRINT_HTML"
      },
      {
        "title": "https://arxiv.org/pdf/1804.09365",
        "url": "https://arxiv.org/pdf/1804.09365",
        "link_type": "ESOURCE|EPRINT_PDF"
      },
      {
        "title": "https://doi.org/10.1051%2F0004-6361%2F201833051",
        "url": "https://doi.org/10.1051%2F0004-6361%2F201833051",
        "link_type": "ESOURCE|PUB_HTML"
      },
      {
        "title": "http://www.aanda.org/10.1051/0004-6361/201833051/pdf",
        "url": "http://www.aanda.org/10.1051/0004-6361/201833051/pdf",
        "link_type": "ESOURCE|PUB_PDF"
      }
    ]
  }
}
```
``````