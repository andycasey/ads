# API

## Data models

These are the top-level data models that most users will need. Their source code actually lives in {obj}`ads.models`, but they are imported to the `ads` namespace for convenience (e.g., {obj}`ads.Document` is imported from {obj}`ads.models.document.Document`).

```{eval-rst}
.. autosummary::
    :toctree: api

    ads.Document
    ads.Library
    ads.Journal
    ads.Affiliation
    ads.Notification
```

All other classes and functions associated with data models live in {obj}`ads.models`.

```{eval-rst}
.. autosummary::
    :toctree: api
    :recursive:

    ads.models
```
   

## Services

ADS offers a [large number of services](https://ui.adsabs.harvard.edu/help/api/api-docs.html#overview). This package exposes the most relevant ones to ADS users. 

Some services have simple API end-points that don't need much more than a HTTP request using {obj}`ads.client.Client`. But for services that have a data model (e.g., the search service ({obj}`ads.services.search`) uses the {obj}`ads.Document` data model), these pages document how queries are translated to the appropriate service and API end-point.  

```{eval-rst}
.. autosummary::
    :toctree: api
    :recursive:

    ads.services
```

## Client

```{eval-rst}
.. autosummary::
    :toctree: api

    ads.client
```

## Exceptions

```{eval-rst}
.. autosummary::

    ads.models.lazy.LazyAttributesWarning
```

## Utilities

```{eval-rst}
.. autosummary::
    :toctree: api
    
    ads.utils
```
