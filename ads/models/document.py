"""
Document data model.
"""
import json
import warnings
from collections import deque
from peewee import (Model, ModelSelect, Expression, ForeignKeyField, VirtualField, fn, ForeignKeyAccessor)

from ads.exceptions import APIResponseError
from ads import logger
from ads.client import Client
from ads.models.base import (ADSAPI, ADSContext)
from ads.models.journal import Journal, JournalField
from ads.models.affiliation import (Affiliation, AffiliationField)
from ads.models.lazy import (DateField, DateTimeField, IntegerField, TextField)
from ads.models.utils import expression_contains


class Document(Model):

    class Meta:
        database = ADSAPI()

    #: A unique identifier for the document, curated by ADS.
    id = IntegerField(help_text="A unique identifier for the document, curated by ADS.")
    #: The document abstract.
    abstract = TextField(help_text="The document abstract.")
    #: Search for a word or phrase in the acknowledgements extracted from fulltexts.
    ack = TextField(help_text="Search for a word or phrase in the acknowledgements extracted from fulltexts.") 
    #: The raw, provided affiliation field.
    aff = TextField(help_text="The raw, provided affiliation field.")
    #: Curated affiliation identifier, parsed from the given affiliation string. See https://ui.adsabs.harvard.edu/blog/affils-update for more details.
    aff_id = TextField(help_text="Curated affiliation identifiers, parsed from the given affiliation string.")
    #: An alternate bibcode.
    alternate_bibcode = TextField(help_text="An alternate bibcode.")
    #: Alternate title, usually present when the original title is not in English.
    alternate_title = TextField(help_text="Alternate title, usually present when the original title is not in English.")
    #: The arXiv class a document was submitted to.
    arxiv_class = TextField(help_text="The arXiv class a document was submitted to.")
    #: Author name.
    author = TextField(help_text="Author name.")
    #: The number of authors.
    author_count = IntegerField(help_text="The number of authors.")
    #: Author name in the form 'Lastname, F'.
    author_norm = TextField(help_text="Author name in the form 'Lastname, F'.")
    #: Document bibliographic code. See https://ui.adsabs.harvard.edu/help/actions/bibcode for more information.
    bibcode = TextField(help_text="Document bibliographic code.")
    #: Records by bibliographic groups, curated by staff outside of ADS.
    bibgroup = TextField(help_text="Records by bibliographic groups, curated by staff outside of ADS.")
    #: Abbreviated name of the journal or publication (e.g., ApJ).
    bibstem = TextField(help_text="Abbreviated name of the journal or publication (e.g., ApJ).")
    #: Search for a word or phrase in (only) the full text.
    body = TextField(help_text="Search for a word or phrase in (only) the full text.") 
    #: The number of citations to this document.
    citation_count = IntegerField(help_text="The number of citations to this document.")
    #: The normalized boost factor.
    cite_read_boost = IntegerField(help_text="The normalized boost factor.")
    #: Related data sources.
    data = TextField(help_text="Related data sources. For example: data:\"CDS\" will return records that have CDS data.")
    #: The database the document resides in (e.g., astronomy or physics).
    database = TextField(help_text="The database the document resides in (e.g., astronomy or physics).")
    #: Publication date, represented by a time format and used for indexing. 
    date = DateTimeField(help_text="Publication date, represented by a time format and used for indexing. For example: date:\"2015-07-01T00:00:00Z\"")
    #: Document type (e.g., article, thesis, etc.
    doctype = TextField(help_text="Search documents by their type: article, thesis, et cetera.")
    #: Digital object identifier
    doi = TextField(help_text="Digital object identifier.")
    #: Electronic identifier of the paper, which is the equivalent of a page number.
    eid = TextField(help_text="Electronic identifier of the paper (equivalent of page number).")
    #: Email addresses of the authors.
    email = TextField(help_text="Search by email addresses for the authors that included them in the article.")
    #: Creation date of the ADS record.
    entry_date = DateTimeField(help_text="Creation date of the ADS record. Note that this can be used like `-entry_date:[NOW-7DAYS TO *]`")
    #: Types of electronic sources available for a record (e.g., ```PUB_HTML```, ```EPRINT_PDF```).
    esources = TextField(help_text="Types of electronic sources available for a record (e.g., pub_html, eprint_pdf).")
    #: Facilities declared in a record, based on a controlled list by AAS journals.
    facility = TextField(help_text="Facilities declared in a record, based on a controlled list by AAS journals.")
    #: Search by grant identifiers and grant agencies (:obj:`ads.Document.grant_id` and :obj:`ads.Document.grant_agencies`).
    grant = TextField(help_text="Search by grant identifiers and grant agencies.")
    #: A field with just the grant agencies name (e.g., NASA).
    grant_agencies = TextField(help_text="A field with just the grant agencies name (e.g., NASA).")
    #: Search by grant identifier.
    grant_id = TextField(help_text="Search by grant identifier.")
    #: Search by an array of alternative identifiers for a record. May contain alternative bibcodes, DOIs, and/or arXiv identifiers.
    identifier = TextField(help_text=(
        "Search by an array of alternative identifiers for a record. May contain alternative bibcodes, "
        "DOIs, and/or arXiv identifiers."
    ))
    #: Datetime when the document was last index by the ADS Solr service.
    indexstamp = DateTimeField(help_text="Datetime when the document was last indexed by the ADS Solr service.")
    #: Find records that contain a curated (ADS-identified) affiliation or institution. See also: :obj:`ads.Document.affiliation`.
    inst = TextField(help_text="Find records that contain a curated (ADS-identified) affiliation or institution. See also: `:obj:Document.affiliation`.")
    #: International Standard Book Number
    isbn = TextField(help_text="International Standard Book Number.")
    #: International Standard Serial NUmber
    issn = TextField(help_text="International Standard Serial Number.")
    #: Issue number of the journal that includes the article.
    issue = TextField(help_text="Issue number of the journal that includes the article.")
    #: An array of normalized and non-normalized keyword values associated with the record.
    keyword = TextField(help_text="An array of normalized and non-normalized keyword values associated with the record.")
    #: The language of the main title.
    lang = TextField(help_text="The language of the main title.")
    #: Information on what linked documents are available.
    links_data = TextField(help_text="Information on what linked documents are available.")
    #: List of NED IDs for a record.
    nedid = TextField(help_text="List of NED IDs for a record.")
    #: Keywords used to describe the NED type (e.g., galaxy, star).
    nedtype = TextField(help_text="Keywords used to describe the NED type (e.g., galaxy, star).")
    #: ORCID claims from users who used the ADS claiming interface.
    orcid_other = TextField(help_text="ORCID claims from users who used the ADS claiming interface.")
    #: ORCIDs supplied by publishers.
    orcid_pub = TextField(help_text="ORCIDs supplied by publishers.")
    #: ORCID claims from users who gave ADS consent to expose their public profile.
    orcid_user = TextField(help_text="ORCID claims from users who gave ADS consent to expose their public profile.")
    #: Page number of a record.
    page = TextField(help_text="Page number of a record.")
    #: The difference between the first and last page numbers in :obj:`ads.Document.page_range`.
    page_count = IntegerField(help_text="If :class:`ads.Document.page_range` is present, it gives the difference between the first and last page numbers in the range.")
    #: An array of miscellaneous flags associated with a record. Examples include: refereed, notrefereed, article, nonarticle, ads_openaccess, eprint_openaccess, pub_openaccess, openaccess, ocrabstract.
    property = TextField(help_text=(
        "An array of miscellaneous flags associated with a record. Examples include: "
        "refereed, notrefereed, article, nonarticle, ads_openaccess, eprint_openaccess, "
        "pub_openaccess, openaccess, ocrabstract"
    ))
    #: The canonical name of the publication that the record appeared in.
    pub = TextField(help_text="The canonical name of the publication that the record appeared in.")
    #: Name of the publisher, but also includes the volume, page, and issue if exists.
    pub_raw = TextField(help_text="Name of the publisher, but also includes the volume, page, and issue if exists.")
    #: Publication date in the form YYYY-MM-DD, where DD will always be '00'.
    pubdate = DateField(help_text="Publication date in the form YYYY-MM-DD, where DD will always be '00'.")
    #: The number of times the record has been viewed within a 90 day window.
    read_count = IntegerField(help_text="The number of times the record has been viewed within a 90 day window.")
    #: List of SIMBAD IDs within a document. This field has privacy restrictions.
    simbid = TextField(help_text="List of SIMBAD IDs within a document. This field has privacy restrictions.")
    #: Keywords used to describe the SIMBAD type.
    simbtype = TextField(help_text="Keywords used to describe the SIMBAD type.")
    #: The title of the record.
    title = TextField(help_text="The title of the record.")
    #: Keywords, 'subject' tags from Vizier.
    vizier = TextField(help_text="Keywords, 'subject' tags from Vizier.")
    #: The journal volume.
    volume = IntegerField(help_text="The journal volume.")
    #: Year of publication.
    year = IntegerField(help_text="Year of publication.")

    # Foreign key fields to local databases.

    #: Any :class:`ads.Affiliation` objects associated with the record, parsed from the :obj:`ads.Document.aff_id` field.
    affiliation = AffiliationField(Affiliation, column_name="__affiliation", lazy_load=True)
    #: The :class:`ads.Journal` associated with the record, parsed from the :obj:`ads.Document.bibcode` field.
    journal = JournalField(Journal, column_name="__journal", lazy_load=True)

    # Virtual fields / operators
    #: Search for a word or phrase in abstract, title, and keywords.
    abs = VirtualField(help_text="Search for a word or phrase in abstract, title, and keywords.")
    #: Search by :obj:`author_norm`, :obj:`alternate_title`, :obj:`bibcode`, :obj:`doi`, and :obj:`identifier`.
    all = VirtualField(help_text="Search by author_norm, alternate_title, bibcode, doi, and identifier.")
    #: Search by arXiv identifier.
    arxiv = VirtualField(help_text="Search by arXiv identifier.")
    #: Search by :obj:`ads.Document.title`, :obj:`ads.Document.abstract`, :obj:`ads.Document.body`, :obj:`ads.Document.keyword`, and :obj:`ads.Document.ack`.
    full = VirtualField(help_text="Search by title, abstract, body, keyword, and ack.")
    #: Search by ORCID identifier, from all possible sources.
    orcid = VirtualField(help_text="ORCID identifier, from all possible sources.")

    # Functions

    @classmethod
    def citations(cls, expression):
        """ Query for documents that cite the documents matching the given query."""
        return fn.citations(expression)

    @classmethod
    def join_citations(cls, expression):
        return fn.joincitations(expression)

    @classmethod
    def pos(cls, expression, position, end_position=None):
        
        end_position = end_position or position
        return fn.pos(expression, position, end_position)

    @classmethod
    def references(cls, expression):
        return fn.references(expression)
    
    @classmethod
    def reviews(cls, expression):
        return fn.reviews(expression)

    @classmethod
    def similar(cls, expression):
        return fn.similar(expression)

    @classmethod
    def top_n(cls, n, expression):
        """
        Return the top `n` documents matching the given expression.
        
        :param n:
            The number of documents to return.
        
        :param expression:
            The expression to query documents.
        """
        return fn.topn(n, expression)
    
    @classmethod
    def trending(cls, expression):
        """
        Query documents that are most read by users who read recent papers on the topic being researched.
        These are papers currently being read by people interested in this field. 
    
        :param expression:
            The expression to search for trending documents.
        """
        return fn.trending(expression)
    
    @classmethod
    def useful(cls, expression):
        return fn.useful(expression)

    @classmethod
    def select(cls, *fields):
        is_default = not fields
        if not fields:
            fields = cls._meta.sorted_fields
        return DocumentSelect(cls, fields, is_default=is_default)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        preferred_key = ("bibcode", "id")
        for key in preferred_key:
            try:
                value = self.__data__[key]
            except IndexError:
                continue
            else:
                break
        else:
            return f"<{self.__class__.__name__}: no identifier>"
        
        return f"<{self.__class__.__name__}: {key}={value}>"

    def _unique_identifier(self):
        keys = ("id", "bibcode")
        for key in keys:
            try:
                value = self.__data__[key]
            except IndexError:
                continue
            else:
                return (getattr(self.__class__, key), value)
        else:
            raise ValueError(f"No identifier found among {keys}")





    
class DocumentSelect(Client, ModelSelect):

    _max_rows = 200
    _row_warning_limit = 10_000
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer = []
        self._count = None
        self._retrieved = 0
        self._iter = 0


    def save(self):
        """
        Save a query on the ADS servers for later execution.
        
        :returns:
            A query identifier returnd by ADS, and the number of documents found.
        """
        response = self.api_request(
            "/vault/query",
            method="post",
            data=json.dumps(self.initial_payload)
        )
        return (response.json["qid"], response.json["numFound"])

    @classmethod
    def load(cls, qid):
        """
        Load a saved query from ADS.
        
        :param qid:
            The query identifier given by ADS when the query was saved
        """
        with cls() as client:
            foo = client.api_request(
                f"/vault/execute_query/{qid}",
                method="get",
                params=dict()
            )
            raise NotImplementedError()
        
        

    def count(self):
        if self._count is None:
            # This is expensive because we are going to have to make a query just to count the rows.
            params = self.cursor_payload.copy()
            params.update(start=0, rows=1, fl=["id"])
            raise NotImplementedError()

        return self._count

    def get(self):
        with self:
            self._create_payloads(rows=1)
            return next(self)

    def get_or_none(self):
        try:
            return self.get()
        except StopIteration:
            return None

    def execute(self):
        return self

    def __iter__(self):
        self._iter = 0
        return self

    def __next__(self):
        while True:
            try:
                document = self._buffer[self._iter]
            except IndexError:
                if self._count is None or self._retrieved < self._count:
                    self.fetch_page()
                else:
                    try:
                        # Close the session before we finish iterating.
                        self.session.close()
                    finally:
                        raise StopIteration
            else:
                self._iter += 1
                return document

        
    def _create_payloads(self, **kwargs):
        fields = []
        for field in self._returning:
            if isinstance(field, str):
                fields.append(field)
            else:
                fields.append(field.name)

        for required_field in ("id", "bibcode"):
            if required_field not in fields:
                fields.append(required_field)

        start = self._offset or 0
        rows = self._limit or self._max_rows

        if self._order_by is not None:
            sort = ", ".join(
                [f"{ordering.node.name} {ordering.direction}" for ordering in self._order_by]
            )
        else:
            sort = None

        payload = dict(
            q=self.__str__(),
            fl=fields,
            fq=None,
            sort=sort,
            start=start,
            rows=rows,
        )
        payload.update(kwargs)
        self._initial_payload = payload
        self._current_payload = payload.copy()


    @property
    def initial_payload(self):
        try:
            return self._initial_payload
        except AttributeError:
            self._create_payloads()
            return self._initial_payload

    @property
    def current_payload(self):
        try:
            return self._current_payload
        except AttributeError:
            self._create_payloads()
            return self._current_payload


    def fetch_page(self):

        logger.debug(f"Querying with {self.current_payload}")
        
        response = self.api_request("/search/query", method="get", params=self.current_payload)

        num_found = response.json["response"]["numFound"]
        documents = response.json["response"]["docs"]

        # If this is the first page, we will store the number of records to expect from this query.
        # TODO: Or should this logic go elsewhere, parsed from something like the `self.last_response`?
        #       or through the API Response object.
        if self._count is None:
            start, rows = (self.current_payload["start"], self.current_payload["rows"])
            self._count = min(num_found - start, rows)
        
        N = 0
        for N, document_kwds in enumerate(documents, start=1):
            self._buffer.append(Document(**document_kwds))

        self._retrieved += N

        logger.debug(f"So far have {self._retrieved} of {self._count}")
        
        # `initial_query` refers to the original query, `query` refers to a mutable query.
        self._current_payload.update(
            start=start + N,
            rows=min(N, self._count - self._retrieved)
        )
        return None


    def __sql__(self, ctx):
        return ctx.sql(self._where)


    def __str__(self):
        db = getattr(self, "_database", None)
        if db is not None:
            ctx = db.get_sql_context()
        else:
            ctx = ADSContext()
        
        query, params = ctx.sql(self).query()
        if not params:
            return query
        
        param = ctx.state.param or "?"
        if param == "?":
            query = query.replace("?", "%s")

        return (query % tuple(params))



# TODO: Docs at https://ui.adsabs.harvard.edu/help/searcfh/comprehensive-solr-term-list
#       say that email can only be viewed with elevated priviledges. I can access it,.. do I have special priviledges,
#       or are is the documentation wrong?

# TODO: ORCID_other and ORCID_user seem very similar. What's the difference?
# TODO: orcid() combined field is not listed at https://ui.adsabs.harvard.edu/help/search/comprehensive-solr-term-list

#first_author = TextField()
#first_author_facet_hier = TextField()
#first_author_norm = TextField()

#citations = VirtualField(
# help_text="Search for documents that are cited by a document."
#)
#pubnote = TextField(
#    help_text="Comments submitted with the arXiv version. This field is not searchable."
#)
#vizier_facet = TextField()

#simbad_object_facet_hier = TextField()

# reference and references seem to be the same according to the docs, but only references works.
#reference = TextField()

# TODO: Need clarity on `bibgroup_facet` from ADS team before we include it here.
# TODO: Need clarity on `author_facet` and `author_facet_hier` from ADS team before we include it here.
#author_facet = TextField(
# help_text="Contains list of names with the number of occurrences that author has for the search."
#)
#author_facet_hier = TextField()
#bibgroup_facet = TextField()    
# TODO: Need clarity on `bibstem_facet` from ADS team before we include it here.
#bibstem_facet = TextField()

# TODO: Not including `classic_factor` because it sounds like the kind of thing that will be deprecated eventually. Check with ADS team.
# classic_factor .. 
# TODO: Not including `copyright` because I can't find any examples of what it is.
#copyright = TextField()
# TODO: Not including `data_facet` because I can't find any examples of what it is.
#data_facet = TextField()

# TODO: Need clarity on this from ADS team.
#doctype_facet_hier = TextField()

# Not including entdate because some artciles don't have it, and it seems that entry_date is the right thing.
#entdate = TextField()

#grant_facet_hier = TextField()
#keyword_facet = TextField()

# Need information on these:    
#keyword_norm = TextField()
#keyword_schema = TextField()

#nedtype_object_facet_hier = TextField()

# Documentation at https://ui.adsabs.harvard.edu/help/search/comprehensive-solr-term-list
# says that page_range is not searchable or viewable. It's at least viewable (e.g., for 2021AcPPA.139..197H it is 197-2018).
# TODO: Should we include it here?

# This field doesn't seem to work at all..
# reader = TextField()


# TODO: When
#recid = TextField()

# For arxiv_class at https://ui.adsabs.harvard.edu/help/search/search-syntax
# the example doesn't work, but arxiv_class:hep-ex does work.

