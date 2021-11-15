import warnings
from functools import cached_property

from .exceptions import APIResponseError

from ads.affiliations import Affiliation

class LazyAttributesWarning(UserWarning):
    pass


class Document(object):

    """ A single record in NASA's Astrophysical Data System. """

    def __init__(self, **kwargs):
        self._raw = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        return None
    
    def __repr__(self):
        return f"<{self._raw.get('bibcode', 'Unknown bibcode')}>"
    
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
        return self._raw.iteritems()

    def _get_field(self, field):
        """
        Query the API for a single field for this document.
        
        This method should only be called indirectly by cached properties.
        
        :param field: 
            name of the record field to query
        """

        # If documents were created from a search query, then we will always have the id.
        # But if they came from a library, we will have the bibcode, but not the id.
        if not hasattr(self, "id") or self.id is None:
            raise APIResponseError("Cannot query for a field without an ID")

        warning = (
            "You're lazily loading document attributes, which makes many calls to the "
            "API. This will impact your rate limits. If you know what document fields "
            "you want ahead of time, provide them as the `fields` keyword argument in "
            "`ads.SearchQuery`."
        )
        warnings.warn(warning, category=LazyAttributesWarning)
        # This is a hack to prevent repeated warnings in IPython.
        # See https://github.com/ipython/ipython/issues/11207
        warnings.simplefilter("ignore", category=LazyAttributesWarning)
        
        # Bad practice to import things within this scope, but it is better for file organisation.
        from ads.search import SearchQuery
        with SearchQuery(q=f"id:{self.id}", fields=[field], rows=1) as q:
            document = next(q)

        if field not in document._raw:
            # If ADS did not send us back the field, then we should just set None to
            # avoid an infinite loop.
            if field in ("reference", "citation", "metrics", "bibtex"):
                raise NotImplementedError("I think this isn't the right way we should do things..")
                pass
            else:
                return None
        value = document.__getattribute__(field)
        self._raw[field] = value
        return value
    
    @cached_property
    def abstract(self):
        """ Document abstract. """
        return self._get_field("abstract")

    @cached_property
    def ack(self):
        """ Acknowledgements. """
        return self._get_field("ack")

    @cached_property
    def aff(self):
        """ Affiliation strings as provided by the authors. """
        return self._get_field("aff")

    @cached_property
    def aff_id(self):
        """ 
        Unique affiliation identifiers parsed by ADS from the author's affiliation strings.

        See https://ui.adsabs.harvard.edu/blog/affils-update for more details.
        """
        return self._get_field("aff_id")


    @cached_property
    def affiliations_identified(self):
        """
        Affiliations identified by ADS from parsing the author's affiliation strings.

        This provides a cleaner representation of author affiliations, because the ADS team
        have parsed affiliation strings and identified the affiliation. For example, there
        are countless variations of how the CfA is described in the author's affiliation.

        While this provides a cleaner representation of author affiliations, it is not
        complete. The distribution of affiliations that are identified will be biased
        in many ways.
        """
        return [[Affiliation(item) for item in aff_id.split("; ")] for aff_id in self.aff_id]


    @cached_property
    def alternate_bibcode(self):
        # TODO
        return self._get_field("alternate_bibcode")

    @cached_property
    def alternate_title(self):
        return self._get_field("alternate_title")

    @cached_property
    def arxiv_class(self):
        return self._get_field("arxiv_class")

    @cached_property
    def author(self):
        return self._get_field("author")

    @cached_property
    def author_count(self):
        return self._get_field("author_count")

    @cached_property
    def author_norm(self):
        return self._get_field("author_norm")

    @cached_property
    def bibcode(self):
        return self._get_field("bibcode")

    @cached_property
    def bibgroup(self):
        return self._get_field("bibgroup")

    @cached_property
    def bibstem(self):
        return self._get_field("bibstem")

    @cached_property
    def citation_count(self):
        return self._get_field("citation_count")

    @cached_property
    def cite_read_boost(self):
        return self._get_field("cite_read_boost")

    @cached_property
    def classic_factor(self):
        return self._get_field("classic_factor")

    @cached_property
    def comment(self):
        return self._get_field("comment")

    @cached_property
    def copyright(self):
        return self._get_field("copyright")

    @cached_property
    def data(self):
        return self._get_field("data")

    @cached_property
    def database(self):
        return self._get_field("database")

    @cached_property
    def date(self):
        return self._get_field("date")

    @cached_property
    def doctype(self):
        return self._get_field("doctype")

    @cached_property
    def doi(self):
        return self._get_field("doi")

    @cached_property
    def eid(self):
        return self._get_field("eid")

    @cached_property
    def entdate(self):
        return self._get_field("entdate")

    @cached_property
    def entry_date(self):
        return self._get_field("entry_date")

    @cached_property
    def esources(self):
        return self._get_field("esources")

    @cached_property
    def facility(self):
        return self._get_field("facility")

    @cached_property
    def first_author(self):
        return self._get_field("first_author")

    @cached_property
    def first_author_norm(self):
        return self._get_field("first_author_norm")

    @cached_property
    def grant(self):
        return self._get_field("grant")

    @cached_property
    def grant_agencies(self):
        return self._get_field("grant_agencies")

    @cached_property
    def grant_id(self):
        return self._get_field("grant_id")

    #@cached_property
    #def id(self):
    #    return self._get_field("id")

    @cached_property
    def identifier(self):
        return self._get_field("identifier")

    @cached_property
    def indexstamp(self):
        return self._get_field("indexstamp")

    @cached_property
    def isbn(self):
        return self._get_field("isbn")

    @cached_property
    def issn(self):
        return self._get_field("issn")

    @cached_property
    def issue(self):
        return self._get_field("issue")

    @cached_property
    def journal(self):
        # Parse from bibcode.
        bibcode = self.bibcode
        raise NotImplementedError("Parsing journal from bibcode is not implemented yet.")

    @cached_property
    def keyword(self):
        return self._get_field("keyword")

    @cached_property
    def keyword_norm(self):
        return self._get_field("keyword_norm")

    @cached_property
    def keyword_schema(self):
        return self._get_field("keyword_schema")

    @cached_property
    def lang(self):
        return self._get_field("lang")

    @cached_property
    def links_data(self):
        return self._get_field("links_data")

    @cached_property
    def nedid(self):
        return self._get_field("nedid")

    @cached_property
    def nedtype(self):
        return self._get_field("nedtype")

    @cached_property
    def orcid_pub(self):
        return self._get_field("orcid_pub")

    @cached_property
    def orcid_other(self):
        return self._get_field("orcid_other")

    @cached_property
    def orcid_user(self):
        return self._get_field("orcid_user")

    @cached_property
    def page(self):
        return self._get_field("page")

    @cached_property
    def page_count(self):
        return self._get_field("page_count")

    @cached_property
    def page_range(self):
        return self._get_field("page_range")

    #@cached_property
    #def property(self):
    #    return self._get_field("property")

    @cached_property
    def pub(self):
        return self._get_field("pub")

    @cached_property
    def pub_raw(self):
        return self._get_field("pub_raw")

    @cached_property
    def pubdate(self):
        return self._get_field("pubdate")

    @cached_property
    def pubnote(self):
        return self._get_field("pubnote")

    @cached_property
    def read_count(self):
        return self._get_field("read_count")

    @cached_property
    def simbid(self):
        return self._get_field("simbid")

    @cached_property
    def title(self):
        return self._get_field("title")

    @cached_property
    def vizier(self):
        return self._get_field("vizier")

    @cached_property
    def volume(self):
        return self._get_field("volume")

    @cached_property
    def year(self):
        return self._get_field("year")


