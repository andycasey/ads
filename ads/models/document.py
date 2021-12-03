"""
Document data model.
"""

from ads.models.base import (DateField, DateTimeField, Model, IntegerField, NodeList, StringField, Function, Expression, OP, ForeignKeyField)
from ads.models.affiliation import Affiliation
from ads.models.journal import Journal

class Document(Model):

    id = IntegerField(
        doc_string="A unique identifier for the document, curated by ADS."
    )
    abstract = StringField(
        doc_string="Search for a word or phrase in an abstract only."
    )
    ack = StringField(
        doc_string="Search for a word or phrase in the acknowledgements extracted from fulltexts."
    )
    aff = StringField(
        doc_string="Search for a word or phrase in the raw, provided affiliation field."
    )
    aff_id = StringField(
        doc_string="Search for documents with a curated affiliation identifier."
    )
    alternate_bibcode = StringField(
        doc_string="Search for documents with an alternate bibcode."
    )
    alternate_title = StringField(
        doc_string="Search for a word of phrase in an alternate title, usually when the original title is not in English."
    )
    arxiv_class = StringField(
        doc_string="Search by which arXiv class a document was submitted to."
    )
    author = StringField(
        doc_string="Search by author name. May include lastname and initial, or stricter author search."
    )
    author_count = IntegerField(
        doc_string="Find records with a specific number of authors, or a range of author counts."
    )
    author_norm = StringField(
        doc_string="Search by author name in the form 'Lastname, F'."
    )
    bibcode = StringField(
        doc_string="Search by bibcode."
    )
    bibgroup = StringField(
        doc_string="Find records by bibliographic groups, curated by staff outside of ADS."
    )
    bibstem = StringField(
        doc_string="Search by the abbreviated name of the journal or publication (e.g., ApJ)."
    )
    body = StringField(
        doc_string="Search for a word or phrase in (only) the full text."
    )
    citation_count = IntegerField(
        doc_string="Find records matching the number of citations, or a range of citations."
    )
    cite_read_boost = IntegerField(
        doc_string="Find records by normalized boost factors, or a range of normalized boost factors."
    )
    data = StringField(
        doc_string="Search by records that have related data. For example: data:\"CDS\" will return records that have CDS data."
    )
    database = StringField(
        doc_string="Find documents by the database the paper resides in (e.g., astronomy or physics)."
    )
    date = DateTimeField(
        doc_string="Publication date, represented by a time format and used for indexing. For example: date:\"2015-07-01T00:00:00Z\""
    )
    doctype = StringField(
        doc_string="Search documents by their type: article, thesis, et cetera."
    )
    doi = StringField(
        doc_string="Digital object identifier."
    )
    eid = StringField(
        doc_string="Electronic identifier of the paper (equivalent of page number)."
    )
    email = StringField(
        doc_string="Search by email addresses for the authors that included them in the article."
    )
    entry_date = DateTimeField(
        doc_string="Creation date of the ADS record. Note that this can be used like `-entry_date:[NOW-7DAYS TO *]`"
    )
    esources = StringField(
        doc_string="Types of electronic sources available for a record (e.g., pub_html, eprint_pdf)."
    )
    facility = StringField(
        doc_string="Facilities declared in a record, based on a controlled list by AAS journals."
    )
    grant = StringField(
        doc_string="Search by grant identifiers and grant agencies."
    )
    grant_agencies = StringField(
        doc_string="A field with just the grant agencies name (e.g., NASA)."
    )
    grant_id = StringField(
        doc_string="Search by grant identifier."
    )
    identifier = StringField(
        doc_string=(
            "Search by an array of alternative identifiers for a record. May contain alternative bibcodes, "
            "DOIs, and/or arXiv identifiers."
        )
    )
    indexstamp = DateTimeField(
        doc_string="Datetime when the document was last indexed by the ADS Solr service."
    )
    inst = StringField(
        doc_string="Find records that contain a curated (ADS-identified) affiliation or institution. See also: `:class:Document.affiliation`."
    )
    isbn = StringField(
        doc_string="International Standard Book Number."
    )
    issn = StringField(
        doc_string="International Standard Serial Number."
    )
    issue = StringField(
        doc_string="Issue number of the journal that includes the article."
    )
    keyword = StringField(
        doc_string="An array of normalized and non-normalized keyword values associated with the record."
    )
    lang = StringField(
        doc_string="The language of the main title."
    )
    links_data = StringField(
        doc_string="Information on what linked documents are available."
    )
    nedid = StringField(
        doc_string="List of NED IDs for a record."
    )
    nedtype = StringField(
        doc_string="Keywords used to describe the NED type (e.g., galaxy, star)."
    )
    orcid_other = StringField(
        doc_string="ORCID claims from users who used the ADS claiming interface."
    )
    orcid_pub = StringField(
        doc_string="ORCIDs supplied by publishers."
    )
    orcid_user = StringField(
        doc_string="ORCID claims from users who gave ADS consent to expose their public profile."
    )
    page = StringField(
        doc_string="Page number of a record."
    )
    page_count = IntegerField(
        doc_string="If `Document.page_range` is present, it gives the difference between the first and last page numbers in the range."
    )
    property = StringField(
        doc_string=(
            "An array of miscellaneous flags associated with a record. Examples include: "
            "refereed, notrefereed, article, nonarticle, ads_openaccess, eprint_openaccess, "
            "pub_openaccess, openaccess, ocrabstract"
        )
    )
    pub = StringField(
        doc_string="The canonical name of the publication that the record appeared in."
    )
    pub_raw = StringField(
        doc_string="Name of the publisher, but also includes the volume, page, and issue if exists."
    )
    pubdate = DateField(
        doc_string="Publication date in the form YYYY-MM-DD, where DD will always be '00'."
    )
    read_count = IntegerField(
        doc_string="The number of times the record has been viewed within a 90 day window."
    )
    simbid = StringField(
        doc_string="List of SIMBAD IDs within a document. This field has privacy restrictions."
    )
    simbtype = StringField(
        doc_string="Keywords used to describe the SIMBAD type."
    )
    title = StringField(
        doc_string="The title of the record."
    )
    vizier = StringField(
        doc_string="Keywords, 'subject' tags from Vizier."
    )
    volume = IntegerField(
        doc_string="The volume of the journal that the article exists in.."
    )
    year = IntegerField(
        doc_string="Year of publication."
    )

    # Virtual fields / operators

    abs = StringField(
        doc_string="Search for a word or phrase in abstract, title, and keywords."
    )
    all = StringField(
        doc_string="Search by `author_norm`, `alternate_title`, `bibcode`, `doi`, and `identifier`.",
    )
    arxiv = StringField(
        doc_string="Search by arXiv identifier."
    )
    citations = Function(
        arguments=("query", ),
        doc_string=(
            "Find records that are cited by a document. For example:\n"
            "`Document.citation == '2015ApJ...808...16N' will return documents that are referenced by 2015ApJ...808...16N.\n"
            "If you want to find papers that cite 2015ApJ...808...16N, use `Document.citations == '2015ApJ...808...16N'`."
        )
    )
    full = StringField(
        doc_string="Search by `title`, `abstract, `body`, `keyword`, and `ack`."
    )
    join_citations = Function(
        name="joincitations", 
        arguments=("query", ),
        doc_string="Equivalent of `Document.references` but implemented using lucene block-join."
    )
    orcid = StringField(
        doc_string="ORCID identifier, from all possible sources."
    )
    pos = Function(
        arguments=("query", "position"),
        keyword_arguments=("end_position", ),
        doc_string=(
            "Search fo an item within a field by specifyin the position in the field.\n"
            "The syntax for this operator is `pos(<query>,<position>,[end_position]). "
            "If no `end_position` is given then it is assumed to be `end_position = position`, "
            "otherwise this performs a query within the range `[position, end_position]`."
        ),
    )
    references = Function(
        arguments=("query", ),
        doc_string="Returns a list of references from given papers."
    )
    reviews = Function(
        arguments=("query", ),
        doc_string=(
            "Find documents citing the most relevant papers on the topic being researched. "
            "These are papers containins the most extensive reviews of the field."
        )
    )
    similar = Function(
        arguments=("query", ),
        doc_string="Return similar documents, based on the similarity of the abstract text."
    )
    top_n = Function(
        name="topn",
        arguments=("n", "query"),
        keyword_arguments=("sort", ),
        doc_string="Return the list of top N documents for a user defined query."
    )
    
    trending = Function(
        arguments=("query", ),
        doc_string=(
            "List of documents most read by users who read recent papers on the topic being researched. "
            "These are papers currently being read by people interested in this field."
        )
    )
    useful = Function(
        arguments=("query", ),
        doc_string=(
            "List of documents frequently cited by the most relevant papers on the topic being researched."
            "These are studies which discuss methods and techniques useful to conduct research in this field."
        )
    )

    # Foreign key fields.
    journal = ForeignKeyField(Journal)


    # TODO: Docs at https://ui.adsabs.harvard.edu/help/searcfh/comprehensive-solr-term-list
    #       say that email can only be viewed with elevated priviledges. I can access it,.. do I have special priviledges,
    #       or are is the documentation wrong?

    # TODO: ORCID_other and ORCID_user seem very similar. What's the difference?
    # TODO: orcid() combined field is not listed at https://ui.adsabs.harvard.edu/help/search/comprehensive-solr-term-list

    #first_author = StringField()
    #first_author_facet_hier = StringField()
    #first_author_norm = StringField()

    #citations = VirtualField(
    # doc_string="Search for documents that are cited by a document."
    #)
    #pubnote = StringField(
    #    doc_string="Comments submitted with the arXiv version. This field is not searchable."
    #)
    #vizier_facet = StringField()

    #simbad_object_facet_hier = StringField()

    # reference and references seem to be the same according to the docs, but only references works.
    #reference = StringField()

    # TODO: Need clarity on `bibgroup_facet` from ADS team before we include it here.
    # TODO: Need clarity on `author_facet` and `author_facet_hier` from ADS team before we include it here.
    #author_facet = StringField(
    # doc_string="Contains list of names with the number of occurrences that author has for the search."
    #)
    #author_facet_hier = StringField()
    #bibgroup_facet = StringField()    
    # TODO: Need clarity on `bibstem_facet` from ADS team before we include it here.
    #bibstem_facet = StringField()

    # TODO: Not including `classic_factor` because it sounds like the kind of thing that will be deprecated eventually. Check with ADS team.
    # classic_factor .. 
    # TODO: Not including `copyright` because I can't find any examples of what it is.
    #copyright = StringField()
    # TODO: Not including `data_facet` because I can't find any examples of what it is.
    #data_facet = StringField()

    # TODO: Need clarity on this from ADS team.
    #doctype_facet_hier = StringField()

    # Not including entdate because some artciles don't have it, and it seems that entry_date is the right thing.
    #entdate = StringField()

    #grant_facet_hier = StringField()
    #keyword_facet = StringField()

    # Need information on these:    
    #keyword_norm = StringField()
    #keyword_schema = StringField()

    #nedtype_object_facet_hier = StringField()
    
    # Documentation at https://ui.adsabs.harvard.edu/help/search/comprehensive-solr-term-list
    # says that page_range is not searchable or viewable. It's at least viewable (e.g., for 2021AcPPA.139..197H it is 197-2018).
    # TODO: Should we include it here?

    # This field doesn't seem to work at all..
    # reader = StringField()
    

    # TODO: When
    #recid = StringField()
    
    # For arxiv_class at https://ui.adsabs.harvard.edu/help/search/search-syntax
    # the example doesn't work, but arxiv_class:hep-ex does work.


    @classmethod
    def has_affiliation(cls, affiliation):
        """
        Return an `:class:ads.models.base.Expression` to select `Document`s with a given `ads.models.Affiliation`.

        :param affiliation:
            A curated affiliation to check for.
        """
        return Expression("aff_id", OP.EQ, affiliation)
    
    @classmethod
    def has_any_affiliation(cls, *affiliations):
        """
        Return an :class:ads.models.base.Expression to select `Document`s with any of the given `ads.models.Affiliations`.
        
        :param affiliations:
            Any number of curated affiliations to check for.
        """
        return Expression("aff_id", OP.IN, NodeList(affiliations, " OR "))
    
    @classmethod
    def has_country_of_affiliation(cls, country):
        """
        Return an :class:ads.models.base.Expression to select Documents with an affiliation from the given country.
        """
        return cls.has_any_affiliation(
            *Affiliation.select().where(Affiliation.country == country).execute()
        )


    def __query__(self, context):
        keys = ("id", "bibcode")
        for key in keys:
            value = self.__data__.get(key, None)
            if value is not None:
                break
        else:
            raise ValueError("No key found in {}".format(keys))
        
        return context.literal(f"{key}:{value}")

    def __eq__(self, rhs):
        return Expression(self, None, None)