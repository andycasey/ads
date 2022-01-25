""" The ADS export document service. """ 
import json
import re
from difflib import get_close_matches
from ads.client import Client
from ads.utils import flatten, _bibcode_regex_pattern
from peewee import Ordering

def ads(*iterable, sort=None) -> str:
    """
    Return a citation string in ADS (generic tagged) format 

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.
    
    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.
    """
    return _export("ads", iterable, sort)

def bibtex(*iterable, max_author=10, author_cutoff=200, key_format=None, journal_format=1, sort=None) -> str:
    """
    Return a citation string in BibTeX format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.
    
    :param max_author: [optional]
        The maximum number of authors displayed. The default value for {obj}`ads.services.export.bibtex` and
        {obj}`ads.services.export.bibtexabs` are different, because the defaults for each end point are different.
    
    :param key_format: [optional]
        Customize bibtex for reference keys using some combination of authors' last name(s), publication year, 
        journal, and bibcode. The user can pick the key generation algorithm by specifying a custom format for it.
        
        For example:

        .. code-block:
        
            Accomazzi:2019              -- %1H:%Y
            Accomazzi:2019:AAS          -- %1H:%Y:%q
            Accomazzi2019               -- %1H%Y
            Accomazzi2019AAS            -- %1H%Y%q
            AccomazziKurtz2019          -- %2H%Y

        The user can specify ``%zm`` to enumerate keys (one character alphabet) if duplicate keys get created.
        Note that if enumeration specifer is not included, then the export service does not enumerate the keys,
        even if duplicate keys are found.

    :param journal_format: [optional]
        An integer flag to decide on the format of the journal name:

        - 1 indicates to use AASTeX macros if there are any (default), otherwise full journal name is exported.
        - 2 indicates to use journal abbreviations,
        - 3 indicates to use full journal name.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    _check_bibtex_inputs(max_author, author_cutoff, key_format, journal_format)
    kwds = dict(maxauthor=max_author, authorcutoaff=author_cutoff, journalformat=journal_format)
    # If we supply a None to keyformat then the export service falls over.
    if key_format is not None:
        kwds["keyformat"] = key_format
    return _export(
        "bibtex", 
        iterable, 
        sort=sort, 
        **kwds
    )

def bibtexabs(*iterable, max_author=0, author_cutoff=200, key_format=None, journal_format=1, sort=None) -> str:
    """
    Return a citation string in BibTeX + abstract format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.
    
    :param max_author: [optional]
        The maximum number of authors displayed. The default value for {obj}`ads.services.export.bibtex` and
        {obj}`ads.services.export.bibtexabs` are different, because the defaults for each end point are different.
    
    :param key_format: [optional]
        Customize bibtex for reference keys using some combination of authors' last name(s), publication year, 
        journal, and bibcode. The user can pick the key generation algorithm by specifying a custom format for it.
        
        For example:
        ```
            Accomazzi:2019              -- %1H:%Y
            Accomazzi:2019:AAS          -- %1H:%Y:%q
            Accomazzi2019               -- %1H%Y
            Accomazzi2019AAS            -- %1H%Y%q
            AccomazziKurtz2019          -- %2H%Y
        ```

        The user can specify ``%zm`` to enumerate keys (one character alphabet) if duplicate keys get created.
        Note that if enumeration specifer is not included, then the export service does not enumerate the keys,
        even if duplicate keys are found.

    :param journal_format: [optional]
        An integer flag to decide on the format of the journal name:

        - 1 indicates to use AASTeX macros if there are any (default), otherwise full journal name is exported.
        - 2 indicates to use journal abbreviations,
        - 3 indicates to use full journal name.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    _check_bibtex_inputs(max_author, author_cutoff, key_format, journal_format)
    # If we supply a None to keyformat then the export service falls over.
    kwds = dict(maxauthor=max_author, authorcutoaff=author_cutoff, journalformat=journal_format)
    if key_format is not None:
        kwds["keyformat"] = key_format
    return _export(
        "bibtexabs", 
        iterable, 
        sort=sort, 
        **kwds
    )

def endnote(*iterable, sort=None) -> str:
    """
    Return a citation string in EndNote format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("endnote", iterable, sort)

def medlars(*iterable, sort=None) -> str:
    """
    Return a citation string in MEDLARS format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("medlars", iterable, sort)

def procite(*iterable, sort=None) -> str:
    """
    Return a citation string in ProCite format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("procite", iterable, sort)

def refworks(*iterable, sort=None) -> str:
    """
    Return a citation string in RefWorks format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("refworks", iterable, sort)

def ris(*iterable, sort=None) -> str:
    """
    Return a citation string in RIS (Refman) format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("ris", iterable, sort)


# The /rss end point is not documented in OpenAPI, but is at https://github.com/adsabs/export_service
# Email the ADS team about this.


def aastex(*iterable, journal_format=1, sort=None) -> str:
    """
    Return a citation string in AASTeX format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param journal_format: [optional]
        An integer flag to decide on the format of the journal name:

        - 1 indicates to use AASTeX macros if there are any (default), otherwise full journal name is exported.
        - 2 indicates to use journal abbreviations,
        - 3 indicates to use full journal name.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    _check_journal_format(journal_format)
    return _export("aastex", iterable, sort, journalformat=journal_format)

def icarus(*iterable, sort=None) -> str:
    """
    Return a citation string in Icarus format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("icarus", iterable, sort)
    
def mnras(*iterable, sort=None) -> str:
    """
    Return a citation string in Monthly Notices of the Royal Astronomical Society format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("mnras", iterable, sort)

def soph(*iterable, sort=None) -> str:
    """
    Return a citation string in Solar Physics (SoPh) format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("soph", iterable, sort)

def dcxml(*iterable, sort=None) -> str:
    """
    Return a citation string in Dublin Core (DC) XML format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("dcxml", iterable, sort)

def refxml(*iterable, sort=None) -> str:
    """
    Return a citation string in REF-XML format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("refxml", iterable, sort)

def refabsxml(*iterable, sort=None) -> str:
    """
    Return a citation string in REFABS-XML format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("refabsxml", iterable, sort)

def votable(*iterable, sort=None) -> str:
    """
    Return a citation string in VOTables format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("votable", iterable, sort)

def csl(*iterable, style, format, sort=None, journal_format=None) -> str:
    """
    Return a citation string in a custom style and format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param style:
        The name of the style to use. This can be one of:

        - aastex
        - icarus
        - mnras
        - soph
        - aspc
        - apsj
        - aasj 
        - ieee

    :param format:
        An integer representing the format to use. This can be one of:

        - ``1`` for Unicode
        - ``2`` for HTML
        - ``3`` for LaTeX

    :param journal_format: [optional]
        An integer flag to decide on the format of the journal name:

        - ``1`` indicates to use AASTeX macros if there are any (default), otherwise full journal name is exported.
        - ``2`` indicates to use journal abbreviations,
        - ``3`` indicates to use full journal name.

        This keyword is only used when one of the following ``style``s is used: ``aastex``, ``aspc``, and ``aasj``.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    # TODO: Check style, format, and journal_format
    style = _check_from_available(style, ("aastex", "icarus", "mnras", "soph", "aspc", "apsj", "aasj", "ieee"))
    _check_journal_format(format, "format")
    _check_journal_format(journal_format)
    return _export("csl", iterable, sort, style=style, format=format, journalformat=journal_format)

def custom(*iterable, format) -> str:
    """
    Return a citation string in a custom format.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param format:
        A custom citation format. For example: "%ZEncoding:latex\\bibitem[]  %l %T (%Y) %q, %V, %p-%P."
    """
    # If we supply `sort="no sort"` to the custom end point, I get a 500 error.
    # Email the ADS team about this.
    return _export("custom", iterable, sort=False, format=format)

def ieee(*iterable, sort=None) -> str:
    """
    Return a citation string in IEEE export (Unicode-encoded).

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects,
        :class:`ads.Library` objects, or strings of bibcodes.

    :param sort: [optional]
        The sorting to apply to the results. This can be ``None`` (no sort), a string like "citation_count desc"),
        or something like `ads.Document.pubdate.desc()`.        
    """
    return _export("ieee", iterable, sort)

def _check_bibtex_inputs(max_author, author_cutoff, key_format, journal_format):
    try:
        int(max_author)
    except:
        raise TypeError(f"`max_author` must be an integer")
    try:
        int(author_cutoff)
    except:
        raise TypeError(f"`author_cutoff` must be an integer")
    try:
        str(key_format)
    except:
        raise TypeError(f"`key_format` must be a string")
    _check_journal_format(journal_format)

def _check_from_available(item, available, case_sensitive=False, strip=True):
    item = item.strip() if strip else item
    for each in available:
        if (case_sensitive and each == item) or (not case_sensitive and each.lower() == item.lower()):
            return each
    close_matches = [f"'{m}'" for m in get_close_matches(item, available)]
    dym_string = ""
    if close_matches:
        dym_string += f"Did you mean {' or '.join(close_matches)}?\n\n"
    raise ValueError(
        f"Unknown value '{item}'. {dym_string}"
        f"All available formats: {', '.join(available)}. "
    )    
    
def _check_journal_format(journal_format, name="journal_format"):
    try:
        journal_format = int(journal_format)
    except:
        raise TypeError(f"`{name}` must be an integer, either 1, 2, or 3")
    else:
        if journal_format not in (1, 2, 3):
            raise ValueError(f"`{name}` must be either 1, 2, or 3")
    
def _export(end_point, iterable, sort, **kwargs):
    bibcode = []
    for item in flatten(iterable):
        try:
            bibcode.append(item.bibcode)
        except AttributeError:
            if isinstance(item, str):
                if not re.match(_bibcode_regex_pattern, item):
                    raise ValueError(f"Invalid bibcode '{item}'")
                bibcode.append(item)
            else:
                raise TypeError(
                    f"Bibcode {item} ({type(item)}) is not a valid bibcode. "
                    f"Supply a string or ads.Document."
                )
    if not bibcode:
        raise ValueError(f"No documents or bibcodes supplied.")
        
    data = dict(bibcode=bibcode)
    if sort is None:
        data["sort"] = "no sort"
    elif sort is False:
        None
    elif isinstance(sort, str):
        data["sort"] = sort
    elif isinstance(sort, Ordering):
        data["sort"] = f"{sort.node.name} {sort.direction}"
    else:
        raise TypeError(f"`sort` must be None, False, a string, or Ordering")
    data.update(kwargs)

    with Client() as client:
        response = client.api_request(
            f"/export/{end_point}", 
            method="post", 
            data=json.dumps(data)
        )
    return response.json["export"]
