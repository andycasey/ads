"""
Sandbox environment that wraps relevant classes so that they receive mock
responses rather than contact the live API
"""

import re

from ads import search
from .search import SearchQuery as _SearchQuery, Article as _Article
from .metrics import MetricsQuery as _MetricsQuery
from .export import ExportQuery as _ExportQuery

from .tests.mocks import MockSolrResponse, MockMetricsResponse, \
    MockExportResponse


class Article(_Article):
    """
    Wrapper for ads.search.Article
    """
    def _get_field(self, field):
        with MockSolrResponse(_SearchQuery.HTTP_ENDPOINT):
            return super(Article, self)._get_field(field)


class SearchQuery(_SearchQuery):
    """
    Wrapper for ads.SearchQuery
    """
    def execute(self):
        with MockSolrResponse(SearchQuery.HTTP_ENDPOINT):
            super(SearchQuery, self).execute()


class MetricsQuery(_MetricsQuery):
    """
    Wrapper for ads.SearchQuery
    """

    def execute(self):
        with MockMetricsResponse(MetricsQuery.HTTP_ENDPOINT):
            return super(MetricsQuery, self).execute()


class ExportQuery(_ExportQuery):
    """
    Wrapper for ads.SearchQuery
    """

    def execute(self):
        with MockExportResponse(re.compile(ExportQuery.HTTP_ENDPOINT)):
            return super(ExportQuery, self).execute()


# Monkey patch relevant classes that are called in ads.search
search.Article = Article
search.MetricsQuery = MetricsQuery
search.ExportQuery = ExportQuery
