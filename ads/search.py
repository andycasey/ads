# coding: utf-8

""" Searching for publications through NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json
import logging
import multiprocessing
import os
import time

# Third party
import requests
import requests_futures.sessions

# Module specific
import parser as parse
from utils import get_dev_key, get_api_settings

__all__ = ['search', 'metadata', 'retrieve_article']

DEV_KEY = get_dev_key()
ADS_HOST = 'http://adslabs.org/adsabs/api/search/'


class Article(object):
    """An object to represent a single publication in NASA's Astrophysical
    Data System."""

    citation_count = 0
    author = ['Anonymous']
    aff = ['Unknown']

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
                .format(bibcode=self.bibcode), rows=200, verbose=True)
            self._references = articles
            return articles

    @property
    def citations(self):
        if hasattr(self, '_citations'):
            return self._citations

        else:
            articles, metadata, request = search("citations(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200, verbose=True)
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




def _build_payload(query=None, authors=None, dates=None, affiliation=None, filter=None,
    fl=None, facet=None, sort='date', order='desc', start=0, rows=20, verbose=False):
    """Builds a dictionary payload for NASA's ADS based on the input criteria."""

    query = parse.query(query, authors, dates)

    # Check inputs
    start = parse.start(start)
    rows = parse.rows(rows)
    sort, order = parse.ordering(sort, order)

    # Filters
    pubdate_filter = parse.dates(dates)
    affiliation_filter = parse.affiliation(affiliation)

    filters = (pubdate_filter, affiliation_filter)
    for query_filter in filters:
        if query_filter is not None:
            query += query_filter

    payload = {
        "q": query,
        "dev_key": DEV_KEY,
        "sort": "{sort} {order}".format(sort=sort.upper(), order=order),
        "start": start,
        "fmt": "json",
        "rows": rows,
        }

    additional_payload = {
        "fl": fl,
        "filter": filter,
        "facet": facet
    }
    for key, value in additional_payload.iteritems():
        if value is None: continue
        payload[key] = value

    return payload


def metadata(query=None, authors=None, dates=None, affiliation=None, filter="database:astronomy",
    fl=None, facet=None, sort='date', order='desc', start=0, rows=1):
    """Search ADS for the given inputs and just return the metadata."""

    payload = _build_payload(**locals())

    r = requests.get(ADS_HOST, params=payload)

    if r.status_code == 200:
        metadata = r.json()["meta"]

        return metadata

    else:
        return r


def search(query=None, authors=None, dates=None, affiliation=None, filter="database:astronomy",
    fl=None, facet=None, sort='date', order='desc', start=0, rows=20, verbose=False):
    """Search ADS and retrieve Article objects."""

    payload = _build_payload(**locals())
    
    r = requests.get(ADS_HOST, params=payload)
    
    if r.status_code == 200:

        results = r.json()
        metadata = results['meta']

        articles = []
        for docinfo in results['results']['docs']:
            articles.append(Article(**docinfo))

        if verbose:
            return (articles, metadata, r)
        return articles

    else:
        if verbose:
            return (False, {"error": r.text}, r)
        return r


def retrieve_article(article, output_filename, clobber=False):
    """Download the journal article (preferred) or pre-print version
    of the article provided, and save the PDF to disk.

    Inputs
    ------
    article : `Article` object
        The article to retrieve.

    output_filename : str
        The filename to save the article to.

    clobber : bool, optional
        Overwrite the filename if it already exists.
    """

    if os.path.exists(output_filename) and not clobber:
        raise IOError("output filename (\"{filename}\") exists and we've been "
            "asked not to clobber it.".format(filename=output_filename))

    # Get the ADS url
    ads_redirect_url = "http://adsabs.harvard.edu/cgi-bin/nph-data_query"
    arxiv_payload = {
        "bibcode": article.bibcode,
        "link_type": "PREPRINT",
        "db_key": "PRE"
    }
    article_payload = {
        "bibcode": article.bibcode,
        "link_type": "ARTICLE",
        "db_key": "AST"
    }
    
    # Let's try and download the article from the journal first
    article_r = requests.get(ads_redirect_url, params=article_payload)

    if not article_r.ok or "Requested scanned pages are not available" in article_r.text:

        # Use the arxiv payload
        arxiv_r = requests.get(ads_redirect_url, params=arxiv_payload)

        if not arxiv_r.ok:
            return False

        article_pdf_url = arxiv_r.url.replace("abs", "pdf")

    else:
        # Parse the PDF url
        article_pdf_url = None
    
    article_pdf_r = requests.get(article_pdf_url)

    if not article_pdf_r.ok: return None

    with open(output_filename, "wb") as fp:
        fp.write(article_pdf_r.content)

    return True


