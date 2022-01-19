""" Document data model. """

from peewee import (Model, VirtualField, fn)

from ads.models.journal import Journal, JournalField
from ads.models.affiliation import (Affiliation, AffiliationField)
from ads.models.lazy import (DateField, DateTimeField, IntegerField, TextField)
from ads.models.utils import ArrayField
from ads.services.search import SearchInterface


class Document(Model):

    """ A document in the SAO/NASA Astrophysics Data System."""

    class Meta:
        database = SearchInterface(None)
    
    #: A unique identifier for the document, curated by ADS.
    id = IntegerField(help_text="A unique identifier for the document, curated by ADS.")
    #: The document abstract.
    abstract = TextField(help_text="The document abstract.", null=True)
    #: Search for a word or phrase in the acknowledgements extracted from fulltexts.
    ack = VirtualField(help_text="Search for a word or phrase in the acknowledgements extracted from fulltexts.") 
    # TODO-> I think ack is a VirtualField (searchable only), but docs don't say that.
    #: The raw, provided affiliation field.
    aff = ArrayField(TextField, help_text="The raw, provided affiliation field.", null=True)
    #: Curated affiliation identifier, parsed from the given affiliation string. See https://ui.adsabs.harvard.edu/blog/affils-update for more details.
    aff_id = ArrayField(TextField, help_text="Curated affiliation identifiers, parsed from the given affiliation string.", null=True)
    #: An alternate bibcode.
    alternate_bibcode = ArrayField(TextField, help_text="An alternate bibcode.", null=True)
    #: Alternate title, usually present when the original title is not in English.
    alternate_title = TextField(help_text="Alternate title, usually present when the original title is not in English.", null=True, default=None)
    #: The arXiv class a document was submitted to.
    arxiv_class = TextField(help_text="The arXiv class a document was submitted to.", null=True)
    #: Author name.
    author = ArrayField(TextField, help_text="Author name.", null=True)
    #author = TextField(help_text="Author name.", null=True)
    #: The number of authors.
    author_count = IntegerField(help_text="The number of authors.", null=True)
    #: Author name in the form 'Lastname, F'.
    author_norm = ArrayField(TextField, help_text="Author name in the form 'Lastname, F'.", null=True)
    #: Document bibliographic code. See https://ui.adsabs.harvard.edu/help/actions/bibcode for more information.
    bibcode = TextField(help_text="Document bibliographic code.")
    #: Records by bibliographic groups, curated by staff outside of ADS.
    bibgroup = TextField(help_text="Records by bibliographic groups, curated by staff outside of ADS.", null=True)
    #: Abbreviated name of the journal or publication (e.g., ApJ).
    bibstem = ArrayField(TextField, help_text="Abbreviated name(s) of the journal or publication (e.g., ApJ).", null=True)
    #: Search for a word or phrase in (only) the full text.
    body = VirtualField(help_text="Search for a word or phrase in (only) the full text.", null=True) 
    #: The number of citations to this document.
    citation_count = IntegerField(help_text="The number of citations to this document.", null=True)
    #: The normalized boost factor.
    cite_read_boost = IntegerField(help_text="The normalized boost factor.", null=True)
    #: Related data sources.
    data = TextField(help_text="Related data sources. For example: data:\"CDS\" will return records that have CDS data.", null=True)
    #: The database the document resides in (e.g., astronomy or physics).
    database = ArrayField(TextField, help_text="The database the document resides in (e.g., astronomy or physics).", null=True)
    #: Publication date, represented by a time format and used for indexing. 
    date = DateTimeField(help_text="Publication date, represented by a time format and used for indexing. For example: date:\"2015-07-01T00:00:00Z\"", null=True)
    #: Document type (e.g., article, thesis, etc.
    doctype = TextField(help_text="Search documents by their type: article, thesis, et cetera.", null=True)
    #: Digital object identifier
    doi = ArrayField(TextField, help_text="Digital object identifier(s).", null=True)
    # TODO: Why is DOI a list? And ISSN, shouldn't these be things where there is only one?
    # Email the ADS team about this.
    #: Electronic identifier of the paper, which is the equivalent of a page number.
    eid = TextField(help_text="Electronic identifier of the paper (equivalent of page number).", null=True)
    #: Email addresses of the authors.
    email = ArrayField(TextField, help_text="Search by email addresses for the authors that included them in the article.", null=True)
    #: Creation date of the ADS record.
    entry_date = DateTimeField(help_text="Creation date of the ADS record. Note that this can be used like `-entry_date:[NOW-7DAYS TO *]`", null=True)
    #: Types of electronic sources available for a record (e.g., ```PUB_HTML```, ```EPRINT_PDF```).
    esources = ArrayField(TextField, help_text="Types of electronic sources available for a record (e.g., pub_html, eprint_pdf).", null=True)
    #: Facilities declared in a record, based on a controlled list by AAS journals.
    facility = ArrayField(TextField, help_text="Facilities declared in a record, based on a controlled list by AAS journals.", null=True)
    #: Search by grant identifiers and grant agencies (:obj:`ads.Document.grant_id` and :obj:`ads.Document.grant_agencies`).
    grant = TextField(help_text="Search by grant identifiers and grant agencies.", null=True)
    # TODO: Is grant and grant_* all virtual fields? I can't find a document that has them. Email the ADS team about this.
    #: A field with just the grant agencies name (e.g., NASA).
    grant_agencies = TextField(help_text="A field with just the grant agencies name (e.g., NASA).", null=True)
    #: Search by grant identifier.
    grant_id = TextField(help_text="Search by grant identifier.", null=True)
    #: Search by an array of alternative identifiers for a record. May contain alternative bibcodes, DOIs, and/or arXiv identifiers.
    identifier = ArrayField(TextField, help_text=(
        "Search by an array of alternative identifiers for a record. May contain alternative bibcodes, "
        "DOIs, and/or arXiv identifiers."
    ))
    #: Datetime when the document was last index by the ADS Solr service.
    indexstamp = DateTimeField(help_text="Datetime when the document was last indexed by the ADS Solr service.")
    #: Find records that contain a curated (ADS-identified) affiliation or institution. See also: :obj:`ads.Document.affiliation`.
    inst = VirtualField(help_text="Find records that contain a curated (ADS-identified) affiliation or institution. See also: `:obj:Document.affiliation`.")
    #: International Standard Book Number
    isbn = TextField(help_text="International Standard Book Number.", null=True)
    #: International Standard Serial NUmber
    issn = ArrayField(TextField, help_text="International Standard Serial Number.", null=True)
    #: Issue number of the journal that includes the article.
    issue = TextField(help_text="Issue number of the journal that includes the article.", null=True)
    #: An array of normalized and non-normalized keyword values associated with the record.
    keyword = TextField(help_text="An array of normalized and non-normalized keyword values associated with the record.", null=True)
    #: The language of the main title.
    lang = TextField(help_text="The language of the main title.", null=True)
    #: Information on what linked documents are available.
    links_data = TextField(help_text="Information on what linked documents are available.", null=True)
    # TODO: links_data is a list of blobs... I think it's viewable but not searchable.
    #: List of NED IDs for a record.
    nedid = ArrayField(TextField, help_text="List of NED IDs for a record.", null=True)
    #: Keywords used to describe the NED type (e.g., galaxy, star).
    nedtype = ArrayField(TextField, help_text="Keywords used to describe the NED type (e.g., galaxy, star).", null=True)
    #: ORCID claims from users who used the ADS claiming interface.
    orcid_other = ArrayField(TextField, help_text="ORCID claims from users who used the ADS claiming interface.", null=True)
    #: ORCIDs supplied by publishers.
    orcid_pub = ArrayField(TextField, help_text="ORCIDs supplied by publishers.", null=True)
    #: ORCID claims from users who gave ADS consent to expose their public profile.
    orcid_user = ArrayField(TextField, help_text="ORCID claims from users who gave ADS consent to expose their public profile.", null=True)
    #: Page number of a record.
    page = ArrayField(TextField, help_text="Page number of a record.", null=True)
    #: The difference between the first and last page numbers in :obj:`ads.Document.page_range`.
    page_count = IntegerField(help_text="If :class:`ads.Document.page_range` is present, it gives the difference between the first and last page numbers in the range.", null=True)
    #: An array of miscellaneous flags associated with a record. Examples include: refereed, notrefereed, article, nonarticle, ads_openaccess, eprint_openaccess, pub_openaccess, openaccess, ocrabstract.
    property = ArrayField(TextField, help_text=(
        "An array of miscellaneous flags associated with a record. Examples include: "
        "refereed, notrefereed, article, nonarticle, ads_openaccess, eprint_openaccess, "
        "pub_openaccess, openaccess, ocrabstract"
    ), null=True)
    #: The canonical name of the publication that the record appeared in.
    pub = TextField(help_text="The canonical name of the publication that the record appeared in.", null=True)
    #: Name of the publisher, but also includes the volume, page, and issue if exists.
    pub_raw = TextField(help_text="Name of the publisher, but also includes the volume, page, and issue if exists.", null=True)
    #: Publication date in the form YYYY-MM-DD, where DD will always be '00'.
    pubdate = DateField(help_text="Publication date in the form YYYY-MM-DD, where DD will always be '00'.", null=True)
    #: The number of times the record has been viewed within a 90 day window.
    read_count = IntegerField(help_text="The number of times the record has been viewed within a 90 day window.", null=True)
    #: List of SIMBAD IDs within a document. This field has privacy restrictions.
    simbid = ArrayField(TextField, help_text="List of SIMBAD IDs within a document. This field has privacy restrictions.", null=True)
    #: Keywords used to describe the SIMBAD type.
    simbtype = ArrayField(TextField, help_text="Keywords used to describe the SIMBAD type.", null=True)
    #: The title of the record.
    title = ArrayField(TextField, help_text="The title of the record.", null=True)
    #: Keywords, 'subject' tags from Vizier.
    vizier = TextField(help_text="Keywords, 'subject' tags from Vizier.", null=True)
    #: The journal volume.
    volume = IntegerField(help_text="The journal volume.", null=True)
    #: Year of publication.
    year = IntegerField(help_text="Year of publication.")

    # Foreign key fields to local databases.

    #: Any :class:`ads.Affiliation` objects associated with the record, parsed from the :obj:`ads.Document.aff_id` field.
    affiliation = AffiliationField(Affiliation, column_name="__affiliation", lazy_load=True, null=True)
    #: The :class:`ads.Journal` associated with the record, parsed from the :obj:`ads.Document.bibcode` field.
    journal = JournalField(Journal, column_name="__journal", lazy_load=True, null=True)

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
        return fn.pos(expression, position, end_position or position)

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

    # Representation

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
            except KeyError:
                continue
            else:
                return (getattr(self.__class__, key), value)
        else:
            raise ValueError(f"No identifier found among {keys}")

