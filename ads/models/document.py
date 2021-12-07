"""
Document data model.
"""
from peewee import Expression, TextField, Model, ForeignKeyField, fn, IntegerField, DateTimeField, DateField

from ads.models.base import (ADSAPI, DocumentSelect)
from ads.models.journal import Journal
from ads.models.affiliation import Affiliation

class Document(Model):

    class Meta:
        database = ADSAPI()

    id = IntegerField(help_text="A unique identifier for the document, curated by ADS.")
    abstract = TextField(help_text="Search for a word or phrase in an abstract only.")
    ack = TextField(help_text="Search for a word or phrase in the acknowledgements extracted from fulltexts.")
    aff = TextField(help_text="Search for a word or phrase in the raw, provided affiliation field.")
    alternate_bibcode = TextField(help_text="Search for documents with an alternate bibcode.")
    alternate_title = TextField(help_text="Search for a word of phrase in an alternate title, usually when the original title is not in English.")
    arxiv_class = TextField(help_text="Search by which arXiv class a document was submitted to.")
    author = TextField(help_text="Search by author name. May include lastname and initial, or stricter author search.")
    author_count = IntegerField(help_text="Find records with a specific number of authors, or a range of author counts.")
    author_norm = TextField(help_text="Search by author name in the form 'Lastname, F'.")
    bibcode = TextField(help_text="Search by bibcode.")
    bibgroup = TextField(help_text="Find records by bibliographic groups, curated by staff outside of ADS.")
    bibstem = TextField(help_text="Search by the abbreviated name of the journal or publication (e.g., ApJ).")
    body = TextField(help_text="Search for a word or phrase in (only) the full text.")
    citation_count = IntegerField(help_text="Find records matching the number of citations, or a range of citations.")
    cite_read_boost = IntegerField(help_text="Find records by normalized boost factors, or a range of normalized boost factors.")
    data = TextField(help_text="Search by records that have related data. For example: data:\"CDS\" will return records that have CDS data.")
    database = TextField(help_text="Find documents by the database the paper resides in (e.g., astronomy or physics).")
    date = DateTimeField(help_text="Publication date, represented by a time format and used for indexing. For example: date:\"2015-07-01T00:00:00Z\"")
    doctype = TextField(help_text="Search documents by their type: article, thesis, et cetera.")
    doi = TextField(help_text="Digital object identifier.")
    eid = TextField(help_text="Electronic identifier of the paper (equivalent of page number).")
    email = TextField(help_text="Search by email addresses for the authors that included them in the article.")
    entry_date = DateTimeField(help_text="Creation date of the ADS record. Note that this can be used like `-entry_date:[NOW-7DAYS TO *]`")
    esources = TextField(help_text="Types of electronic sources available for a record (e.g., pub_html, eprint_pdf).")
    facility = TextField(help_text="Facilities declared in a record, based on a controlled list by AAS journals.")
    grant = TextField(help_text="Search by grant identifiers and grant agencies.")
    grant_agencies = TextField(help_text="A field with just the grant agencies name (e.g., NASA).")
    grant_id = TextField(help_text="Search by grant identifier.")
    identifier = TextField(help_text=(
        "Search by an array of alternative identifiers for a record. May contain alternative bibcodes, "
        "DOIs, and/or arXiv identifiers."
    ))
    indexstamp = DateTimeField(help_text="Datetime when the document was last indexed by the ADS Solr service.")
    inst = TextField(help_text="Find records that contain a curated (ADS-identified) affiliation or institution. See also: `:class:Document.affiliation`.")
    isbn = TextField(help_text="International Standard Book Number.")
    issn = TextField(help_text="International Standard Serial Number.")
    issue = TextField(help_text="Issue number of the journal that includes the article.")
    keyword = TextField(help_text="An array of normalized and non-normalized keyword values associated with the record.")
    lang = TextField(help_text="The language of the main title.")
    links_data = TextField(help_text="Information on what linked documents are available.")
    nedid = TextField(help_text="List of NED IDs for a record.")
    nedtype = TextField(help_text="Keywords used to describe the NED type (e.g., galaxy, star).")
    orcid_other = TextField(help_text="ORCID claims from users who used the ADS claiming interface.")
    orcid_pub = TextField(help_text="ORCIDs supplied by publishers.")
    orcid_user = TextField(help_text="ORCID claims from users who gave ADS consent to expose their public profile.")
    page = TextField(help_text="Page number of a record.")
    page_count = IntegerField(help_text="If `Document.page_range` is present, it gives the difference between the first and last page numbers in the range.")
    property = TextField(help_text=(
        "An array of miscellaneous flags associated with a record. Examples include: "
        "refereed, notrefereed, article, nonarticle, ads_openaccess, eprint_openaccess, "
        "pub_openaccess, openaccess, ocrabstract"
    ))
    pub = TextField(help_text="The canonical name of the publication that the record appeared in.")
    pub_raw = TextField(help_text="Name of the publisher, but also includes the volume, page, and issue if exists.")
    pubdate = DateField(help_text="Publication date in the form YYYY-MM-DD, where DD will always be '00'.")
    read_count = IntegerField(help_text="The number of times the record has been viewed within a 90 day window.")
    simbid = TextField(help_text="List of SIMBAD IDs within a document. This field has privacy restrictions.")
    simbtype = TextField(help_text="Keywords used to describe the SIMBAD type.")
    title = TextField(help_text="The title of the record.")
    vizier = TextField(help_text="Keywords, 'subject' tags from Vizier.")
    volume = IntegerField(help_text="The volume of the journal that the article exists in..")
    year = IntegerField(help_text="Year of publication.")

    # Foreign key fields

    aff_id = ForeignKeyField(
        Affiliation.id,
        help_text="Search for documents with a curated affiliation identifier."
    )
    affiliation = ForeignKeyField(Affiliation, column_name="aff_id") # Helper function    
    journal = ForeignKeyField(Journal)

    # Virtual fields / operators

    abs = TextField(help_text="Search for a word or phrase in abstract, title, and keywords.")
    all = TextField(help_text="Search by `author_norm`, `alternate_title`, `bibcode`, `doi`, and `identifier`.",)
    arxiv = TextField(help_text="Search by arXiv identifier.")
    full = TextField(help_text="Search by `title`, `abstract, `body`, `keyword`, and `ack`.")
    orcid = TextField(help_text="ORCID identifier, from all possible sources.")

    # Functions

    @classmethod
    def citations(cls, expression):
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
        return fn.topn(n, expression)
    
    @classmethod
    def trending(cls, expression):
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

