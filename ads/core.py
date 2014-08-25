# coding: utf-8

""" A Python tool for interacting with NASA's ADS """

__author__ = "Andy Casey <andy@astrowizici.st>"

# Standard library
import os
import warnings

# Third party
import requests
import requests_futures.sessions

# Module specific
import parser, utils

API_MAX_ROWS = 200
DEV_KEY = utils.get_dev_key()
ADS_HOST = "http://adslabs.org/adsabs/api"

__all__ = ["Article", "query", "metrics", "metadata", "retrieve_article"]

class Article(object):
    """An object to represent a single publication in NASA's Astrophysical
    Data System."""

    aff = ["Unknown"]
    author = ["Anonymous"]
    keyword = []
    citation_count = 0
    reference_count = 0
    url = None

    def __init__(self, **kwargs):
        # It's not Pythonic to use '[citations]' as an attribute so start by
        # remapping that.
        kwargs[u"reference_count"] = (kwargs.pop(u"[citations]", {})
                                      .pop(u"num_references", 0))

        # Save the raw dictionary of attributes for later use.
        self._raw = kwargs

        # Update this object to have attributes for everything in attribute
        # dictionary.
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        if "bibcode" in kwargs:
            self.url = "http://adsabs.harvard.edu/abs/{0}".format(kwargs["bibcode"])

        return None

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        return u"<{0} {1} {2}, {3}>".format(self.author[0].split(",")[0],
            "" if len(self.author) == 1 else (u" & {0}".format(
                self.author[1].split(",")[0]) if len(self.author) == 2 else "et al."),
            self.year, self.bibcode)

    def __repr__(self):
        return u"<ads.{0} object at {1}>".format(self.__class__.__name__, hex(id(self)))

    def __getitem__(self, k):
        return self._raw[k]

    def keys(self):
        return self._raw.keys()

    def items(self):
        return self._raw.items()

    def iteritems(self):
        return self._raw.iteritems()

    @property
    def bibtex(self):
        """Return a BiBTeX entry for the current article."""

        all_entry_types = "ARTICLE, INPROCEEDINGS, PHDTHESIS, MASTERSTHESIS, "\
            "NONARTICLE, EPRINT, BOOK, PROCEEDINGS, CATALOG, SOFTWARE".split(", ")

        # Find the entry type
        entry_type = [entry_type in self.property for entry_type in all_entry_types]
        if not any(entry_type):
            raise TypeError("article entry type not recognised")

        entry_type = all_entry_types[entry_type.index(True)]

        # Is it an EPRINT? If so, mark as ARTICLE and use arXiv as journal
        if entry_type == "EPRINT":
            entry_type = "ARTICLE"

        elif entry_type in ("NONARTICLE", "CATALOG", "SOFTWARE"):
            entry_type = "MISC"

        """
        TYPE = [required, [optional]]

        article = [author, title, journal, year, [volume, number, pages, month, note, key]]
        book = [author or editor, title, publisher, year, [volume, series, address, edition, month, note, key]]
        inproceedings = [author, title, booktitle, year, [editor, pages, organization, publisher, address, month, note, key]]
        MASTERSTHESIS = [author, title, school, year, [address, month, note, key]]
        misc = [[author, title, howpublished ,month, year, note, key]]
        phdthesis = [author, title, school, year, [address, month, note, key]]
        proceedings = [title, year, [editor, publisher, organization, address, month, note, key]]
        """

        _ = lambda item: "{{{0}}}".format(item)
        months = {
            0: '', 1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may',
            6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dec'
        }
        parsers = {
            "author":           lambda article: _(" and \n".join([" and ".join(["{{{0}}}, {1}".format(author.split(",")[0], "~".join(["{0}.".format(name[0]) \
                                    for name in author.split(",")[1].split()])) for author in article.author[i:i+4]]) for i in xrange(0, len(article.author), 4)])),
            "month":            lambda article: months[int(article.pubdate.split("-")[1])],
            "pages":            lambda article: _(article.page[0]),
            "title":            lambda article: "{{{{{0}}}}}".format(article.title[0]),
            "journal":          lambda article: _(article.pub),
            "year":             lambda article: _(article.year),
            "volume":           lambda article: _(article.volume),
            "adsnote":          lambda article: "{Provided by the SAO/NASA Astrophysics Data System API}",
            "adsurl":           lambda article: _("http:/adsabs.harvard.edu/abs/{0}".format(article.bibcode)),
            "keywords":         lambda article: _(", ".join(article.keyword)),
            "doi":              lambda article: _(article.doi[0]),
            "eprint":           lambda article: _("arXiv:{0}".format(article.identifier[["astro-" in i for i in article.identifier].index(True)]))
        }

        # Create start of BiBTeX
        bibtex = ["@{0}{{{1}".format(entry_type, self.bibcode)]

        if entry_type == "ARTICLE":
            required_entries = ["author", "title", "journal", "year"]
            optional_entries = ["volume", "pages", "month", "adsnote", "adsurl", "doi", "eprint", "keywords"]

        elif entry_type == "BOOK":
            required_entries = ["author", "title", "publisher", "year"]
            optional_entries = ["volume", "issue", "month", "adsurl"]

        elif entry_type == "INPROCEEDINGS":
            required_entries = ["author", "title", "year"]
            optional_entries = ["pages", "publisher", "month", "adsurl"]

        elif entry_type == "PROCEEDINGS":
            required_entries = ["title", "year"]
            optional_entries = ["publisher", "month"]

        else:
            # We should retrieve it from the ADS page.
            raise NotImplementedError

        for required_entry in required_entries:
            try:
                value = parsers[required_entry](self)
                if value:
                    bibtex.append("{0} = {1}".format(required_entry.rjust(9), value))
            except:
                raise TypeError("could not generate {0} BibTeX entry for {1}".format(
                    required_entry, self.bibcode))

        for optional_entry in optional_entries:
            try:
                value = parsers[optional_entry](self)
                if value:
                    bibtex.append("{0} = {1}".format(optional_entry.rjust(9), value))
            except: pass

        return ",\n".join(bibtex) + "\n}\n"


    @property
    def references(self):
        """Retrieves reference list for the current article and stores them."""
        if not hasattr(self, '_references'):
            self._references = list(search("references(bibcode:{bibcode})".format(
                bibcode=self.bibcode), rows="all"))
        return self._references


    @property
    def citations(self):
        """Retrieves citation list for the current article and stores them."""
        if not hasattr(self, '_citations'):
            self._citations = list(search("citations(bibcode:{bibcode})".format(
                bibcode=self.bibcode), rows="all"))
        return self._citations


    @property
    def metrics(self):
        """Retrieves metrics for the current article and stores them."""

        if not hasattr(self, "_metrics"):
            url = "{0}/record/{1}/metrics/".format(ADS_HOST, self.bibcode)
            payload = {"dev_key": DEV_KEY}

            r = requests.get(url, params=payload)
            if not r.ok: r.raise_for_status()

            # Prettify the metrics to Python objects
            self._metrics = utils.pythonify_metrics_json(r.json())
        return self._metrics


    def build_reference_tree(self, depth=1, **kwargs):
        """
        Builds a reference tree for this paper.

        :param depth: [optional]
            The number of levels to fetch in the reference tree.

        :type depth:
            int

        :param kwargs: [optional]
            Keyword arguments to pass to ``ads.search``.


        :returns:
            A list of references to the current article, with pre-loaded
            references down by ``depth``.
        """

        try: depth = int(depth)
        except TypeError:
            raise TypeError("depth must be an integer-like type")

        if depth < 1:
            raise ValueError("depth must be a positive integer")

        session = requests_futures.sessions.FuturesSession()

        # To understand recursion, first you must understand recursion.
        level = [self]
        total_articles = len(level) - 1
        kwargs.setdefault("rows", "all")

        for level_num in xrange(depth):

            level_requests = [search("references(bibcode:{bibcode})".format(
                bibcode=article.bibcode), **kwargs) for article in level]

            # Complete all requests
            new_level = []
            for request, article in zip(level_requests, level):
                setattr(article, "_references", list(request))
                new_level.extend(article.references)

            level = sum([new_level], [])
            total_articles += len(level)

        return self._references


    def build_citation_tree(self, depth=1, **kwargs):
        """
        Builds a citation tree for this paper.

        :param depth: [optional]
            The number of levels to fetch in the citation tree.

        :type depth:
            int

        :param kwargs: [optional]
            Keyword arguments to pass to ``ads.search``.


        :returns:
            A list of citation to the current article, with pre-loaded
            citation down by ``depth``.
        """

        try: depth = int(depth)
        except TypeError:
            raise TypeError("depth must be an integer-like type")

        if depth < 1:
            raise ValueError("depth must be a positive integer")

        session = requests_futures.sessions.FuturesSession()

        # To understand recursion, first you must understand recursion.
        level = [self]
        total_articles = len(level) - 1
        kwargs.setdefault("rows", "all")

        for level_num in xrange(depth):

            level_requests = [search("citations(bibcode:{bibcode})".format(
                bibcode=article.bibcode), **kwargs) for article in level]

            # Complete all requests
            new_level = []
            for request, article in zip(level_requests, level):
                setattr(article, "_citations", list(request))
                new_level.extend(article.citations)

            level = sum([new_level], [])
            total_articles += len(level)

        return self._citations


class APIError(Exception):
    """Exception class for ADS API errors"""
    pass


class query(object):
    """Query ADS and retrieve Article objects"""

    def __init__(self, query=None, title=None, authors=None, dates=None, 
        affiliation=None, affiliation_pos=None, acknowledgements=None, fl=None, 
        facet=None, sort="date", order="desc", start=0, rows=20,
        database="astronomy or physics", property=None, **kwargs):

        if "author" in kwargs.keys() and authors is None:
            authors = kwargs["author"]

        arguments = locals().copy()
        del arguments["self"]

        self.payload = _build_payload(**arguments)
        self.session = requests_futures.sessions.FuturesSession()

        self.active_requests = [self.session.get(ADS_HOST + "/search/",
            params=self.payload)]
        self.retrieved_articles = []

        # Do we have to perform more queries?
        if rows == "all" or rows > API_MAX_ROWS:

            # Get metadata from serial request
            metadata_payload = self.payload.copy()
            metadata_payload["rows"] = 1
            r = requests.get(ADS_HOST + "/search/", params=metadata_payload)
            if not r.ok: r.raise_for_status()
            metadata = r.json()["meta"]

            # Should we issue a warning about excessive rows retrieved?
            if metadata["hits"] >= 10000:
                long_query_message = "ADS query is retrieving more than 10,000"\
                    " records. Use ads.metadata to find the number of rows for"\
                    " a search query before executing it with ads.search"
                warnings.warn(long_query_message)

            # Are there enough rows such that we actually have to make more requests?
            if API_MAX_ROWS >= metadata["hits"]: return

            if rows == "all":
                num_additional_queries = int(metadata["hits"]/API_MAX_ROWS)
                if not metadata["hits"] % API_MAX_ROWS: num_additional_queries -= 1

            else:
                num_additional_queries = int(rows/API_MAX_ROWS)
                if not rows % API_MAX_ROWS: num_additional_queries -= 1

            # Initiate future requests
            for i in xrange(1, num_additional_queries + 1):
                # Update payload to start at new point
                self.payload["start"] = i * API_MAX_ROWS

                # Limit total number of rows if required
                if rows != "all" and (i + 1) * API_MAX_ROWS > rows:
                    self.payload["rows"] = rows - i * API_MAX_ROWS

                self.active_requests.append(self.session.get(ADS_HOST \
                    + "/search/", params=self.payload))

    def __iter__(self):
        return self

    def next(self):

        if len(self.active_requests) == 0 and len(self.retrieved_articles) == 0:
            self.session.executor.shutdown()
            raise StopIteration

        if len(self.retrieved_articles) == 0:
            active_request = self.active_requests.pop(0)
            response = active_request.result().json()

            if "error" in response:
                raise APIError(response["error"])

            self.retrieved_articles.extend([Article(**article_info) \
                for article_info in response["results"]["docs"]])

        if len(self.retrieved_articles) == 0:
            self.session.executor.shutdown()
            raise StopIteration

        return self.retrieved_articles.pop(0)


def search(*args, **kwargs):
    """ ads.search is deprecated; you should use ads.query from now on """

    warnings.warn("ads.search will be deprecated in v1.0. Please use ads.query instead.",
        DeprecationWarning)
    return query(*args, **kwargs)


def metrics(author, dates=None, database="astronomy or physics", rows=20,
    metadata=False):
    """ Retrieves metrics for a given author query. """

    payload = _build_payload(authors=author, database=database, rows=rows)
    r = requests.get(ADS_HOST + "/search/metrics/", params=payload)
    if not r.ok: r.raise_for_status()

    contents = r.json()
    if "error" in contents:
        raise APIError(contents["error"])
    metadata, results = contents["meta"], utils.pythonify_metrics_json(contents["results"])

    if metadata:
        return (results, metadata)
    return results


def metadata(query=None, title=None, authors=None, dates=None, affiliation=None,
    affiliation_pos=None, database="astronomy or physics"):
    """Search ADS for the given inputs and just return the metadata."""

    payload = _build_payload(**locals())
    payload["rows"] = 1 # It's meta-data, baby.
    r = requests.get(ADS_HOST + "/search/", params=payload)
    if not r.ok: r.raise_for_status()

    contents = r.json()
    if "error" in contents:
        raise APIError(contents["error"])
    return contents["meta"]


def _build_payload(query=None, title=None, authors=None, dates=None,
    affiliation=None, affiliation_pos=None, fl=None, acknowledgements=None,
    facet=None, sort="date", order="desc", start=0, rows=20,
    database="astronomy or physics", property=None, **kwargs):
    """Builds a dictionary payload for NASA's ADS based on the input criteria."""

    q = parser.query(query, title, authors)

    # Check inputs
    start, rows = parser.rows(start, rows, max_rows=API_MAX_ROWS)
    sort, order = parser.ordering(sort, order)

    # Filters
    pubdate_filter = parser.dates(dates)
    affiliation_filter = parser.affiliation(affiliation, affiliation_pos)
    acknowledgements_filter = parser.acknowledgements(acknowledgements)
    # You shouldn't ever use 'property' since it's special, but we're being consistent with ADS
    properties_filter = parser.properties(property)

    q += " ".join([each for each in (pubdate_filter, affiliation_filter, acknowledgements_filter,
        properties_filter) if each is not None])

    payload = {
        "q": q,
        "dev_key": DEV_KEY,
        "sort": "{sort} {order}".format(sort=sort.upper(), order=order),
        "start": start,
        "fmt": "json",
        "rows": rows,
    }
    additional_payload = {
        "fl": fl,
        "filter": parser.database(database),
        "facet": facet
    }
    payload.update(additional_payload)

    return payload


def retrieve_article(article, output_filename, clobber=False):
    """
    Download the journal article (preferred) or pre-print version of the article
    provided, and save the PDF to disk.

    :param article:
        The article to retrieve.

    :type article:
        :class:`ads.Article`

    :param output_filename:
        The path to save the PDF article to.

    :type output_filename:
        str

    :param clobber: [optional]
        Clobber the existing ``output_filename`` if it already exists.

    :type clobber:
        bool

    :returns:
        ``True`` when the article has downloaded.

    :raise IOError:
        If the ``output_filename`` exists and ``clobber`` is set to ``False``.
    """

    if os.path.exists(output_filename) and not clobber:
        raise IOError("output filename ({filename}) exists and we've been "
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

    if not article_r.ok:

        arxiv_r = requests.get(ads_redirect_url, params=arxiv_payload)
        if not arxiv_r.ok:
            arxiv_r.raise_for_status()

        article_pdf_url = arxiv_r.url.replace("abs", "pdf")

    else:
        # Parser the PDF url
        article_pdf_url = article_r.url.rstrip("+html")

    article_pdf_r = requests.get(article_pdf_url)
    if not article_pdf_r.ok:
        article_pdf_r.raise_for_status()

    with open(output_filename, "wb") as fp:
        fp.write(article_pdf_r.content)

    return True
