# coding: utf-8

""" Searching for publications through NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json
import logging
import multiprocessing
import time

# Third party
import requests
import requests_futures.sessions

# Module specific
from utils import get_dev_key, get_api_settings

__all__ = ['search']

DEV_KEY = get_dev_key()
ADS_HOST = 'http://adslabs.org/adsabs/api/search/'


class Article(object):
    """An object to represent a single publication in NASA's Astrophysical
    Data System."""

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        return None

    # TODO __repr__

    # TODO bibtex @property

    @property
    def references(self):
        if hasattr(self, '_references'):
            return self._references

        else:
            articles, metadata, request = search("references(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200)
            self._references = articles
            return articles

    @property
    def citations(self):
        if hasattr(self, '_citations'):
            return self._citations

        else:
            articles, metadata, request = search("citations(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200)
            self._citations = articles
            return articles


    def build_reference_tree(self, depth):
        """Builds a reference tree for this paper.

        Inputs
        ------
        depth : int
            The number of levels to fetch in the reference tree.

        Returns
        -------
        num_articles_in_tree : int
            The total number of referenced articles in the reference tree.
        """

        try: depth = int(depth)
        except TypeError:
            raise TypeError("depth must be an integer-like type")

        if depth < 1:
            raise ValueError("depth must be a positive integer")

        session = requests_futures.sessions.FuturesSession()

        # To understand recursion, first you must understand recursion.
        level = [self]
        total_articles = len(level)

        for level_num in xrange(depth):

            level_requests = []
            for article in level:
                payload = _build_payload("references(bibcode:{bibcode})"
                    .format(bibcode=article.bibcode))

                level_requests.append(session.get(ADS_HOST, params=payload))

            # Complete all requests
            new_level = []
            for request, article in zip(level_requests, level):
                data = request.result().json()["results"]["docs"]

                setattr(article, "_references", [Article(**doc_info) for doc_info in data])
                new_level.extend(article.references)

            level = sum([new_level], [])
            total_articles += len(level)

        return total_articles          


    def build_citation_tree(self, depth):
        """Builds a citation tree for this paper.

        Inputs
        ------
        depth : int
            The number of levels to fetch in the citation tree.

        Returns
        -------
        num_articles_in_tree : int
            The total number of cited articles in the citation tree.
        """

        try: depth = int(depth)
        except TypeError:
            raise TypeError("depth must be an integer-like type")

        if depth < 1:
            raise ValueError("depth must be a positive integer")

        session = requests_futures.sessions.FuturesSession()

        # To understand recursion, first you must understand recursion.
        level = [self]
        total_articles = len(level)

        for level_num in xrange(depth):

            level_requests = []
            for article in level:
                payload = _build_payload("citations(bibcode:{bibcode})"
                    .format(bibcode=article.bibcode))

                level_requests.append(session.get(ADS_HOST, params=payload))

            # Complete all requests
            new_level = []
            for request, article in zip(level_requests, level):
                data = request.result().json()["results"]["docs"]

                setattr(article, "_citations", [Article(**doc_info) for doc_info in data])
                new_level.extend(article.citations)

            level = sum([new_level], [])
            total_articles += len(level)

        return total_articles     




def _build_payload(query=None, author=None, year=None, sort='date', order='desc',
    start=0, rows=20):
    """Builds a dictionary payload for NASA's ADS based on the input criteria."""

    query_refinements = []

    # Check rows
    if rows == 'max':
        # This checks your settings based on your developer API key

        rows = get_api_settings(DEV_KEY)["max_rows"]

    else:
        try: rows = int(rows)
        except TypeError:
            raise TypeError("rows must be an integer-like type")

        if rows < 1:
            raise ValueError("rows must be a positive integer")

    # Verify year
    if isinstance(year, (list, tuple)):
        if len(year) > 2:
            raise ValueError("if year is specified as a list, it must"
                " be as '(start, end)', either of which can be empty")

        if len(year) == 1:
            start_year, end_year = (year[0], None)

        else:
            start_year, end_year = year

        # Ensure they are integer-types
        # TODO: Months will come later
        check_years = {
            'start': start_year,
            'end':   end_year
        }
        for label in check_years:
            if check_years[label] is not None:
                try: check_years[label] = int(check_years[label])
                except TypeError:
                    raise TypeError("{label} year must be integer-like type or None"
                        .format(label=label))

            else:
                check_years[label] = '*'

        # Check that end comes after start
        if start_year is not None and end_year is not None \
        and start_year > end_year:
            raise ValueError("end year cannot be after the start year")

        # If both years are None then filter nothing.
        if start_year is not None or end_year is not None:
            query_refinements.append('year:[{start_year} TO {end_year}]'
                .format(start_year=check_years['start'], end_year=check_years['end']))

    elif isinstance(year, (str, unicode)):

        # We will accept '2002-', '2002..', '..2003', '2002..2003'
        # '2002.01..2002.08', '2002.04..', '2002/07', '2002-7', '2002-07

        raise NotImplementedError

    elif isinstance(year, (float, int)):
        # Should be float or integer
        # TODO: Months will come later

        year = int(year)
        query_refinements.append('year:{year}'.format(year=year))

    else:
        if year is not None:
            raise TypeError("year type not understood")

    try:
        start = int(start)
    except TypeError:
        raise TypeError("start must be an integer-like type")

    if start < 0:
        raise ValueError("start must be positive")

    if order.lower() not in ('asc', 'desc'):
        raise ValueError("order must be either 'asc' or 'desc'")

    acceptable_sorts = ("date", "relevance", "cited", "popularity")
    if sort.lower() not in acceptable_sorts:
        raise ValueError("sort must be one of: {acceptable_sorts}"
            .format(acceptable_sorts=', '.join(acceptable_sorts)))

    if len(query_refinements) > 0:
        query += ' ' + ' '.join(query_refinements)

    payload = {
        "q": query,
        "dev_key": DEV_KEY,
        "sort": "{sort} {order}".format(sort=sort.upper(), order=order),
        "start": start,
        "fmt": "json",
        "rows": rows
        }

    return payload


def search(query=None, author=None, year=None, sort='date', order='desc',
    start=0, rows=20):
    """Search ADS and retrieve Article objects."""

    payload = _build_payload(**locals())

    r = requests.get(ADS_HOST, params=payload)

    if r.status_code == 200:

        results = r.json()
        metadata = results['meta']

        articles = []
        for docinfo in results['results']['docs']:
            articles.append(Article(**docinfo))

        return (articles, metadata, r)



    else:
        return r # For debugging -- remove this later
        return (False, {
                'error': r.text
            })