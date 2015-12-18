"""
Interface to the adsws search api.
"""

import warnings
import six
import math
from werkzeug.utils import cached_property
import json

from .config import SEARCH_URL
from .exceptions import SolrResponseParseError, APIResponseError
from .base import BaseQuery, APIResponse
from .metrics import MetricsQuery
from .export import ExportQuery


class Article(object):
    """
    An object to represent a single record in NASA's Astrophysical
    Data System.
    """
    # Due to the desire to have load-on-demand and to expose data such as
    # Article.metrics, this class has dependencies on search.py and other core
    # services; this is why it is currently impossible for it to live in
    # base.py, which is the most logical place for it.
    def __init__(self, **kwargs):
        """
        :param kwargs: Set object attributes from kwargs
        """

        self._raw = kwargs
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

    def __str__(self):
        if six.PY3:
            return self.__unicode__()
        return self.__unicode__().encode("utf-8")

    def __unicode__(self):
        author = self.first_author or "Unknown author"
        if self.author and len(self.author) > 1:
            author += " et al."

        return u"<{author} {year}, {bibcode}>".format(
            author=author,
            year=self.year,
            bibcode=self.bibcode,
        )

    def __eq__(self, other):
        if (not hasattr(self, 'bibcode') or not hasattr(other, 'bibcode') or
                self.bibcode is None or other.bibcode is None):
            raise TypeError("Cannot compare articles without bibcodes")
        return self.bibcode == other.bibcode

    def __ne__(self, other):
        return not self.__eq__(other)

    def keys(self):
        return self._raw.keys()

    def items(self):
        return self._raw.items()

    def iteritems(self):
        return six.iteritems(self._raw)

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

    def _get_field(self, field):
        """
        Queries the api for a single field for the record by `id`.
        This method should only be called indirectly by cached properties.
        :param field: name of the record field to load
        """
        if not hasattr(self, "id") or self.id is None:
            raise APIResponseError("Cannot query an article without an id")
        sq = next(SearchQuery(q="id:{}".format(self.id), fl=field))
        # If the requested field is not present in the returning Solr doc,
        # return None instead of hitting _get_field again.
        if field not in sq._raw:
            return None
        value = sq.__getattribute__(field)
        self._raw[field] = value
        return value

    @cached_property
    def abstract(self):
        return self._get_field('abstract')

    @cached_property
    def aff(self):
        return self._get_field('aff')

    @cached_property
    def author(self):
        return self._get_field('author')

    @cached_property
    def citation_count(self):
        return self._get_field('citation_count')

    @cached_property
    def bibstem(self):
        return self._get_field('bibstem')

    @cached_property
    def database(self):
        return self._get_field('database')

    @cached_property
    def identifier(self):
        return self._get_field('identifier')

    @cached_property
    def first_author_norm(self):
        return self._get_field('first_author_norm')

    @cached_property
    def issue(self):
        return self._get_field('issue')

    @cached_property
    def keyword(self):
        return self._get_field('keyword')

    @cached_property
    def page(self):
        return self._get_field('page')

    @cached_property
    def property(self):
        return self._get_field('property')

    @cached_property
    def pub(self):
        return self._get_field('pub')

    @cached_property
    def pubdate(self):
        return self._get_field('pubdate')

    @cached_property
    def read_count(self):
        return self._get_field('read_count')

    @cached_property
    def reference(self):
        return self._get_field('reference')

    @cached_property
    def citation(self):
        return self._get_field('citation')

    @cached_property
    def title(self):
        return self._get_field('title')

    @cached_property
    def volume(self):
        return self._get_field('volume')

    @cached_property
    def year(self):
        return self._get_field('year')
    
    @cached_property
    def orcid_pub(self):
        """ORCiD identifiers assigned by publishers"""
        return self._get_field('orcid_pub')
    
    @cached_property
    def orcid_user(self):
        """ORCiD claims by ADS verified users."""
        return self._get_field('orcid_user')
    
    @cached_property
    def orcid_other(self):
        """ORCiD claims by everybody else."""
        return self._get_field('orcid_other')
    
    @cached_property
    def metrics(self):
        return MetricsQuery(bibcodes=self.bibcode).execute()

    @cached_property
    def bibtex(self):
        """Return a BiBTeX entry for the current article."""
        return ExportQuery(bibcodes=self.bibcode, format="bibtex").execute()


class SolrResponse(APIResponse):
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
            self.fl = self.params.get('fl', [])
            if isinstance(self.fl, six.string_types):
                self.fl = self.fl.split(',')
            self.response = self.json['response']
            self.numFound = self.response['numFound']
            self.docs = self.response['docs']
        except KeyError as e:
            raise SolrResponseParseError("{}".format(e))

    @property
    def articles(self):
        """
        articles getter
        """
        if self._articles is None:
            self._articles = []
            for doc in self.docs:
                # ensure all fields in the "fl" are in the doc to address
                # issue #38
                for k in set(self.fl).difference(doc.keys()):
                    doc[k] = None
                self._articles.append(Article(**doc))
        return self._articles


class SearchQuery(BaseQuery):
    """
    Represents a query to apache solr
    """
    HTTP_ENDPOINT = SEARCH_URL
    DEFAULT_FIELDS = ["author", "first_author", "bibcode", "id", "year",
                      "title", "reference", "citation"]

    def __init__(self, query_dict=None, q=None, fq=None, fl=DEFAULT_FIELDS,
                 sort=None, start=0, rows=50, max_pages=1, **kwargs):
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
            be modified after instantiation to increase the number of results
        :param kwargs: kwargs to add to `q` as "key:value"
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
            if sort is not None:
                sort = sort if " " in sort else "{} desc".format(sort)
            _ = {
                "q": q or '',
                "fq": fq,
                "fl": fl,
                "sort": sort,
                "start": start,
                "rows": rows,
            }
            # Filter out None values
            self._query = dict(
                (k, v) for k, v in six.iteritems(_) if v is not None
            )

            # Include `id` as a field, always (could be None, string or list)
            self._query.setdefault("fl", ["id"])
            if isinstance(self._query["fl"], six.string_types):
                _ = map(str.strip, self._query["fl"].split(","))
                self._query["fl"] = ["id"] + list(_)
            else:
                self._query["fl"] = ["id"] + self._query["fl"]

            # Format and add kwarg (key, value) pairs to q
            if kwargs:
                _ = ['{}:"{}"'.format(k, v) for k, v in six.iteritems(kwargs)]
                self._query['q'] = '{} {}'.format(self._query['q'], ' '.join(_))

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
        return self.__next__()

    def __next__(self):
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

            # if we have hit the max_pages limit, then iteration is done.
            page = math.ceil(len(self.articles)/self.query['rows'])
            if page >= self.max_pages:
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
        Sends the http request implied by the self.query
        In addition, set up the request such that we can call next()
        to provide the next page of results
        """
        self.response = SolrResponse.load_http_response(
            self.session.get(self.HTTP_ENDPOINT, params=self.query)
        )
        self._articles.extend(self.response.articles)
        self._query['start'] += self._query['rows']


class query(SearchQuery):
    """
    Backwards compatible proxy to SearchQuery
    """
    def __init__(self, *args, **kwargs):
        """
        Override parent's __init__ to show the deprecation warning
        """
        warnings.warn(
            "ads.query will be deprectated. Use ads.SearchQuery in the future",
            DeprecationWarning
        )
        if isinstance(args[0], six.string_types):
            kwargs.update({'q': args[0]})
            args = args[1:]
        super(self.__class__, self).__init__(*args, **kwargs)
