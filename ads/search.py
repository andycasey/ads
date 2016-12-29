"""
Interface to the adsws search api.
"""

import warnings
import six
import math

from .config import SEARCH_URL
from .exceptions import SolrResponseParseError, APIResponseError
from .base import BaseQuery, APIResponse
from .metrics import MetricsQuery
from .export import ExportQuery
from .utils import cached_property


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
        author = self._raw.get("first_author", "Unknown author")
        if len(self._raw.get("author", [])) > 1:
            author += " et al."

        return u"<{author} {year}, {bibcode}>".format(
            author=author,
            year=self._raw.get("year", "Unknown year"),
            bibcode=self._raw.get("bibcode", "Unknown bibcode")
        )

    def __eq__(self, other):
        if self._raw.get("bibcode") is None or other._raw.get("bibcode") is None:
            raise TypeError("Cannot compare articles without bibcodes")
        return self._raw['bibcode'] == other._raw['bibcode']

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
            # These fields will never be in the result solr document;
            # pass through to __getattribute__ to allow the relevant
            # secondary service queries
            if field in ["reference", "citation", "metrics", "bibtex"]:
                pass
            else:
                return None
        value = sq.__getattribute__(field)
        self._raw[field] = value
        return value

    @cached_property
    def abstract(self):
        return self._get_field('abstract')

    @cached_property
    def ack(self):
        return self._get_field('ack')

    @cached_property
    def aff(self):
        return self._get_field('aff')

    @cached_property
    def alternate_bibcode(self):
        return self._get_field('alternate_bibcode')

    @cached_property
    def alternate_title(self):
        return self._get_field('alternate_title')

    @cached_property
    def arxiv_class(self):
        return self._get_field('arxiv_class')

    @cached_property
    def author(self):
        return self._get_field('author')

    @cached_property
    def citation_count(self):
        return self._get_field('citation_count')

    @cached_property
    def bibcode(self):
        return self._get_field('bibcode')

    @cached_property
    def bibgroup(self):
        return self._get_field('bibgroup')

    @cached_property
    def copyright(self):
        return self._get_field('copyright')

    @cached_property
    def data(self):
        return self._get_field('data')

    @cached_property
    def database(self):
        return self._get_field('database')

    @cached_property
    def doctype(self):
        return self._get_field('doctype')

    @cached_property
    def doi(self):
        return self._get_field('doi')

    @cached_property
    def identifier(self):
        return self._get_field('identifier')

    @cached_property
    def indexstamp(self):
        return self._get_field('indexstamp')

    @cached_property
    def first_author(self):
        return self._get_field('first_author')

    @cached_property
    def grant(self):
        return self._get_field('grant')

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
        q = SearchQuery(
            q='references(id:{})'.format(self.id),
            fl=['id', 'bibcode']
        )
        return [a.bibcode for a in q]

    @cached_property
    def citation(self):
        q = SearchQuery(
            q='citations(id:{})'.format(self.id),
            fl=['id', 'bibcode']
        )
        return [a.bibcode for a in q]

    @cached_property
    def title(self):
        return self._get_field('title')

    @cached_property
    def vizier(self):
        return self._get_field('vizier')

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
        warnings.warn("metrics should be queried with ads.MetricsQuery(); You will"
                      "hit API ratelimits very quickly otherwise.", UserWarning)
        return MetricsQuery(bibcodes=self.bibcode).execute()

    @cached_property
    def bibtex(self):
        """Return a BiBTeX entry for the current article."""
        warnings.warn("bibtex should be queried with ads.ExportQuery(); You will "
                      "hit API ratelimits very quickly otherwise.", UserWarning)
        return ExportQuery(bibcodes=self.bibcode, format="bibtex").execute()


class SolrResponse(APIResponse):
    """
    Base class for storing a solr response
    """

    def __init__(self, http_response):
        """
        De-serialize a json string representing a solr response
        :param http_response: complete json response from solr
        :type http_response: request.response
        """
        self._raw = http_response.text
        self.json = http_response.json()
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
                      "title"]

    def __init__(self, query_dict=None, q=None, fq=None, fl=DEFAULT_FIELDS,
                 sort=None, cursorMark=None, start=None, rows=50, max_pages=1,
                 token=None, **kwargs):
        """
        The constructor is designed to set valid and useful
        query params with potentially sparsely/selectively defined arguments

        :param query_dict: raw query that will be sent unmodified. raw takes
            precedence over individually defined query params
        :type query_dict: dict
        :param q: solr "q" param (query)
        :param fq: solr "fq" param (filter query)
        :param fl: solr "fl" param (filter limit)
        :param sort: solr "sort" param (sort)
        :param cursorMark: solr "cursorMark" param
        :param start: solr "start" param (start) (discouraged; use cursorMark)
        :param rows: solr "rows" param (rows)
        :param max_pages: Maximum number of pages to return. This value may
            be modified after instantiation to increase the number of results
        :param token: optional API token to use for this searchquery
        :param kwargs: kwargs to add to `q` as "key:value"
        """
        self._articles = []
        self.response = None  # current SolrResponse object
        self.max_pages = max_pages
        self.__iter_counter = 0  # Counter for our custom iterator method

        if query_dict is not None:
            query_dict.setdefault('rows', 50)
            query_dict.setdefault('cursorMark', '*')
            query_dict.setdefault('sort', 'score desc,id desc')
            self._query = query_dict
        else:
            if start is None and cursorMark is None:
                cursorMark = "*"
            if sort is None and start is None:
                sort = "score desc,id desc"
            elif sort is None and start is not None:
                sort = "score desc"
            else:
                sort = sort.replace("+", " ")
                sort = sort if " " in sort else "{} desc".format(sort)
                # cursors require unique field in the sort
                if "id" not in sort and start is None:
                    sort = "{},id desc".format(sort)
            _ = {
                "q": q or '',
                "fq": fq,
                "fl": fl,
                "sort": sort,
                "start": start,
                "cursorMark": cursorMark,
                "rows": int(rows),
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

            # remove bibtex and metrics as a safeguard against
            # https://github.com/andycasey/ads/issues/73
            for field in ["bibtex", "metrics"]:
                if field in self._query["fl"]:
                    self.query["fl"].remove(field)

            # Format and add kwarg (key, value) pairs to q
            if kwargs:
                _ = [u'{}:"{}"'.format(k, v) for k, v in six.iteritems(kwargs)]
                self._query['q'] = u'{} {}'.format(self._query['q'], ' '.join(_))

        assert self._query.get('rows') > 0, "rows must be greater than 0"
        assert self._query.get('q'), "q must not be empty"
        assert self._query.get('cursorMark') is None or \
            self._query.get('start') is None, \
            "cursorMark and start are mutually exclusive parameters"

        if token is not None:
            self.token = token

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

        # ADS will apply a ceiling to 'rows' and re-write the query
        # This code checks if that happened by comparing the reponse
        # "rows" with what we sent in our query
        # references https://github.com/andycasey/ads/issues/45
        recv_rows = int(self.response.responseHeader.get("params", {}).get("rows"))
        if recv_rows != self.query.get("rows"):
            self._query['rows'] = recv_rows
            warnings.warn("Response rows did not match input rows. "
                          "Setting this query's rows to {}".format(self.query['rows']))

        self._articles.extend(self.response.articles)
        if self._query.get('start') is not None:
            self._query['start'] += self._query['rows']
        elif self._query.get('cursorMark') is not None:
            self._query['cursorMark'] = self.response.json.get("nextCursorMark")


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
