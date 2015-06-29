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

    def __eq__(self, other):
        if self.bibcode is None or other.bibcode is None:
            raise TypeError("Cannot compare articles without bibcodes")
        return self.bibcode == other.bibcode

    def __ne__(self, other):
        return not self.__eq__(other)

    def keys(self):
        return self._raw.keys()

    def items(self):
        return self._raw.items()

    def iteritems(self):
        return self._raw.iteritems()

    @property
    def bibtex(self):
        """Return a BiBTeX entry for the current article."""
        raise NotImplementedError

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


class BaseQuery(object):
    """
    Represents an arbitrary query to the adsws-api
    """

    def set_token(self, token=None):
        """
        set the instance attribute `token` following the following logic,
        stopping whenever a token is found. Raises NoTokenFound is no token
        is found
        1. method argument `token`
        2. environment variable ADS_DEV_KEY
        3. file containg plaintext ADS_DEV_KEY as the contents in ~/.ads/key

        :param token: plaintext token
        """
        if token is not None:
            self.token = token
            return

        # TODO: Implement

    def __call__(self):
        return self.execute()

    def execute(self):
        """
        Each subclass should define their own execute method
        """
        raise NotImplementedError


