"""
Core interface to the adsws-api. Each class is responsible for interfacing
to a adsws-api backend service: They should base class `BaseQuery` and
implement an `execute()` method.
"""

import warnings
import requests

from .config import SEARCH_URL
from .models import BaseQuery, SolrResponse


class SearchQuery(BaseQuery):
    """
    Represents a query to apache solr
    """
    api_endpoint = SEARCH_URL

    def __init__(self, raw=None, q=None, fq=None, fl=None, sort=None,
                 start=None, rows=None):
        """
        constructor
        :param raw: raw string that will be sent unmodified. raw takes
            precedence over individually defined query params
        :param q: solr "q" param (query)
        :param fq: solr "fq" param (filter query)
        :param fl: solr "fl" param (filter limit)
        :param sort: solr "sort" param (sort)
        :param start: solr "start" param (start)
        :param rows: solr "rows" param (rows)
        """
        self.articles = []
        self.sr = None  # current SolrResponse object
        self.page = None  # Highest page that we've queried

        self.raw = raw
        if self.raw is None:
            self.q = q
            self.fq = fq
            self.fl = fl
            self.sort = sort
            self.start = start
            self.rows = rows

    def __iter__(self):
        return self

    def execute(self):
        """
        Sends the http request implied by the instance attributes.
        In addition, set up prepared requests such that we can call next()
        to provide the next page of results
        """
        self.sr = SolrResponse.load_http_response(requests.get(self.url))
        self.articles.extend(self.sr.articles)


class ExportQuery(BaseQuery):
    """
    Represents a query to the adsws export service
    """
    def __init__(self):
        raise NotImplementedError


class BigQuery(BaseQuery):
    """
    Represents a query to the adsws bigquery service
    """
    def __init__(self):
        raise NotImplementedError


class VisQuery(BaseQuery):
    """
    Represents a query to the adsws visualizations service
    """
    def __init__(self):
        raise NotImplementedError


class MetricsQuery(BaseQuery):
    """
    Represents a query to the adsws metrics service
    """
    def __init__(self):
        raise NotImplementedError


class query(SearchQuery):
    """
    Backwards compatible proxy to SearchQuery
    """
    def __init__(self, *args, **kwargs):
        """
        Override parent's __init__ to show the deprecation warning
        """
        warnings.warn(
            "ads.query will be deprectated. Use ads.SearchQuery in the future",
            DeprecationWarning
        )
        super(self.__class__, self).__init__(*args, **kwargs)


