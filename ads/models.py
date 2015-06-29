"""
ADS API data models
"""

import json

from ads.exceptions import SolrResponseParseError


class SolrResponse(object):
    """
    Base class for storing a solr response
    """

    def __init__(self, raw):
        """
        De-serialize a json string representing a solr response
        :param raw: complete json response from solr
        :type raw: basestring
        """
        self._raw = raw
        self.json = json.loads(raw)
        self._articles = None
        try:
            self.responseHeader = self.json['responseHeader']
            self.params = self.json['responseHeader']['params']
            self.response = self.json['response']
            self.numFound = self.response['numFound']
            self.docs = self.response['docs']
        except KeyError, e:
            raise SolrResponseParseError("{}".format(e))

    @classmethod
    def load_http_response(cls, HTTPResponse):
        """
        Returns an instansiated SolrResponse using data in a requests.response.
        Sets class attribute `articles` to a list containing Article instances.
        :param HTTPResponse: response object
        :type HTTPResponse: requests.Response
        :return SolrResponse instance
        """
        HTTPResponse.raise_for_status()
        c = cls(HTTPResponse.text)
        c.articles  # The getter will set this attribute
        return c

    @property
    def articles(self):
        """
        articles getter
        """
        if self._articles is None:
            self._articles = []
            for doc in self.docs:
                self._articles.append(Article(**doc))
        return self._articles

    @articles.setter
    def articles(self, value):
        """
        transparent .articles setter
        """
        self._articles = value


class Article(object):
    """
    An object to represent a single record in NASA's Astrophysical
    Data System.
    """

    # define these class attributes; these are expected to exist
    # by various instance methods
    _references = None
    _citations = None
    _bibtex = None
    first_author = None
    author_norm = []
    year = None
    bibcode = None

    def __init__(self, **kwargs):
        """
        :param kwargs: Set object attributes from kwargs
        """
        self._raw = kwargs

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        author = self.first_author or "Unknown author"
        if len(self.author_norm) > 1:
            author = "{} et al.".format(author)

        return u"<{author} {year}, {bibcode}>".format(
            author=author,
            year=self.year,
            bibcode=self.bibcode,
        )

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
        raise NotImplementedError


    @property
    def citations(self):
        """Retrieves citation list for the current article and stores them."""
        raise NotImplementedError

    @property
    def metrics(self):
        """Retrieves metrics for the current article and stores them."""
        raise NotImplementedError


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

        raise NotImplementedError


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

        raise NotImplementedError