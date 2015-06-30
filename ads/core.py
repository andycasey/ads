"""
Core interface to the adsws-api. Each class is responsible for interfacing
to a adsws-api backend service: They should base class `BaseQuery` and
implement an `execute()` method.
"""

import warnings
import math

from .config import SEARCH_URL
from .models import BaseQuery, SolrResponse


class SearchQuery(BaseQuery):
    """
    Represents a query to apache solr
    """
    api_endpoint = SEARCH_URL

    def __init__(self, query_dict=None, q=None, fq=None, fl=None, sort=None,
                 start=0, rows=50, max_pages=3):
        """
        constructor
        :param query_dict: raw query that will be sent unmodified. raw takes
            precedence over individually defined query params
        :type query_dict: dict
        :param q: solr "q" param (query)
        :param fq: solr "fq" param (filter query)
        :param fl: solr "fl" param (filter limit)
        :param sort: solr "sort" param (sort)
        :param start: solr "start" param (start)
        :param rows: solr "rows" param (rows)
        :param max_pages: Maximum number of pages to return. This value may
            be modified after instansiation to increase the number of results
        """
        self._articles = []
        self.response = None  # current SolrResponse object
        self.max_pages = max_pages
        self.__iter_counter = 0  # Counter for our custom iterator method
        if query_dict is not None:
            query_dict.setdefault('rows', 50)
            query_dict.setdefault('start', 0)
            self._query = query_dict
        else:
            # Construct query from kwargs and filter out None values
            _ = {
                "q": q,
                "fq": fq,
                "fl": fl,
                "sort": sort,
                "start": start,
                "rows": rows,
            }
            self._query = dict(
                (k, v) for k, v in _.iteritems() if v is not None
            )
        assert self._query.get('rows') > 0, "rows must be greater than 0"
        assert self._query.get('q'), "q must not be empty"

    @property
    def articles(self):
        """
        Read-only articles attribute should not be modified directly, as
        it is used to gauge the progress of the query
        """
        return self._articles

    @property
    def progress(self):
        """
        Returns a string representation of the progress of the search such as
        "1234/5000", which refers to the number of results retrived / the
        total number of results found
        """
        if self.response is None:
            return "Query has not been executed"
        return "{}/{}".format(len(self.articles), self.response.numFound)

    @property
    def query(self):
        """
        Read-only query attribute should only be created at init. Create
        a new class instance to modify a query.
        SearchQuery.query represents the *next* query that will be executed
        """
        return self._query

    def __iter__(self):
        return self

    def next(self):
        """
        iterator method, for backwards compatibility with the list() workflow
        """
        # Allow immediate iteration without forcing a user to call .execute()
        # explicitly
        if self.response is None:
            self.execute()

        try:
            cur = self._articles[self.__iter_counter]
            # If no more articles, check to see if we should query for the
            # next page of results
        except IndexError:
            # If we already have all the results, then iteration is done.
            if len(self.articles) >= self.response.numFound:
                raise StopIteration("All records found")

            # if we have hit the max_pages limit, the iteration is done.
            page = math.ceil(len(self.articles)/self.query['rows'])
            if page > self.max_pages:
                raise StopIteration("Maximum number of pages queried")

            # We aren't on the max_page of results nor do we have all
            # results: execute the next query and yield from the newly
            # extended .articles array.
            self.execute()
            cur = self._articles[self.__iter_counter]

        self.__iter_counter += 1
        return cur

    def execute(self):
        """
        Sends the http request implied by the instance attributes.
        In addition, set up prepared requests such that we can call next()
        to provide the next page of results
        """
        self.response = SolrResponse.load_http_response(
            self.session.get(self.api_endpoint, params=self._query)
        )
        self._articles.extend(self.response.articles)
        self._query['start'] += self._query['rows']


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
        Override parent's __init__ to show the deprecation warning and
        re-construct the old query API into the newer SearchQuery api
        """
        warnings.warn(
            "ads.query will be deprectated. Use ads.SearchQuery in the future",
            DeprecationWarning
        )
        # TODO implement title, author kwargs
        super(self.__class__, self).__init__(*args, **kwargs)


