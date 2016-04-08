"""
A selection of utility functions
"""

from pprint import pprint

from .search import SearchQuery
from .metrics import MetricsQuery
from .export import ExportQuery


def get_ratelimits(pretty_print=False):
    """
    Get all the rate limits for all endpoints
    """

    endpoints = [SearchQuery, MetricsQuery, ExportQuery]
    all_ratelimits = {}

    for endpoint in endpoints:
        ratelimits = endpoint.get_ratelimits()

        name = endpoint.__name__.replace('Query', '').lower()
        all_ratelimits['/{}'.format(name)] = ratelimits

    if pretty_print:
        pprint(all_ratelimits)
    else:
        return all_ratelimits
