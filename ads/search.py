# coding: utf-8

""" Searching for publications through NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json
import logging

# Third party
import requests

# Module specific
from utils import get_dev_key

__all__ = ['search']

DEV_KEY = get_dev_key()
ADS_HOST = 'http://adslabs.org/adsabs/api/search/'


class Article(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        return None

    def get_references(self):
        raise NotImplementedError

    def get_citations(self):
        #&q=references(bibcode:2011ApSSP...1..125H)

        self.citations = search("citations(bibcode:{bibcode})"
            .format(bibcode=self.bibcode), rows=200)


def search(query=None, author=None, year=None, sort='date', order='desc',
    start=0, rows=20):
    """Search ADS and retrieve Article objects."""

    query_refinements = []

    # Check rows
    if rows == 'max':

        raise NotImplementedError

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