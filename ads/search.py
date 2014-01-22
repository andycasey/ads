# coding: utf-8

""" Searching for publications through NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

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

__all__ = ["Article", "search", "metrics", "metadata", "retrieve_article"]

DEV_KEY = get_dev_key()
ADS_HOST = "http://adslabs.org/adsabs/api"


class Article(object):
    """An object to represent a single publication in NASA's Astrophysical
    Data System."""

    aff = ["Unknown"]
    author = ["Anonymous"]
    citation_count = 0
    url = None

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        if "bibcode" in kwargs:
            self.url = "http://adsabs.harvard.edu/abs/{0}".format(kwargs["bibcode"])

        return None


    #__str__ should be readable
    def __str__(self):
        return "<{0} {1} {2}, {3}>".format(self.author[0].split(",")[0],
            "" if len(self.author) == 1 else (" & {0}".format(self.author[1].split(",")[0]) if len(self.author) == 2 else "et al."),
            self.year, self.bibcode)
    
    #__repr__ should be unambiguous
    def __repr__(self):
        return "<ads.{0} object at {1}>".format(self.__class__.__name__, hex(id(self)))


    # TODO bibtex @property


    @property
    def references(self):
        """Retrieves reference list for the current article and stores them."""
        if hasattr(self, '_references'):
            return self._references

        else:
            articles, metadata, request = search("references(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200, verbose=True)
            self._references = articles
            return articles


    @property
    def citations(self):
        """Retrieves citation list for the current article and stores them."""
        if hasattr(self, '_citations'):
            return self._citations

        else:
            articles, metadata, request = search("citations(bibcode:{bibcode})"
                .format(bibcode=self.bibcode), rows=200, verbose=True)
            self._citations = articles
            return articles


    @property
    def metrics(self):
        """Retrieves metrics for the current article and stores them."""

        if hasattr(self, "_metrics"):
            return self._metrics

        url = "{0}/record/{1}/metrics/".format(ADS_HOST, self.bibcode)
        payload = {"dev_key": DEV_KEY}

        r = requests.get(url, params=payload)
        if not r.ok: r.raise_for_status()

        self._metrics = r.json()
        return self._metrics


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

                level_requests.append(session.get(ADS_HOST + "/search/", params=payload))

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

                level_requests.append(session.get(ADS_HOST + "/search/", params=payload))

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


def metrics(author, verbose=False, **kwargs):
    """ Retrieves metrics for a given author query """

    payload = {
        "q": author,
        "dev_key": DEV_KEY,
    }
    r = requests.get(ADS_HOST + "/search/metrics/", params=payload)
    if not r.ok: r.raise_for_status()
    
    contents = r.json()
    metadata, results = contents["meta"], contents["results"]

    if verbose:
        return (results, metadata, r)
    return results


def metadata(query=None, authors=None, dates=None, affiliation=None, filter="database:astronomy",
    fl=None, facet=None, sort='date', order='desc', start=0, rows=1):
    """Search ADS for the given inputs and just return the metadata."""

    payload = _build_payload(**locals())
    r = requests.get(ADS_HOST + "/search/", params=payload)
    if not r.ok: r.raise_for_status()
    
    metadata = r.json()["meta"]
    return metadata


def search(query=None, authors=None, dates=None, affiliation=None, filter="database:astronomy",
    fl=None, facet=None, sort='date', order='desc', start=0, rows=20, verbose=False):
    """Search ADS and retrieve Article objects."""

    payload = _build_payload(**locals())
    r = requests.get(ADS_HOST + "/search/", params=payload)
    if not r.ok: r.raise_for_status()

    results = r.json()
    metadata = results['meta']

    articles = []
    for docinfo in results['results']['docs']:
        articles.append(Article(**docinfo))

    if verbose:
        return (articles, metadata, r)
    return articles


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
    if not article_pdf_r.ok: article_pdf_r.raise_for_status()

    with open(output_filename, "wb") as fp:
        fp.write(article_pdf_r.content)

    return True


