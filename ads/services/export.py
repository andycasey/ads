import json
import re
from difflib import get_close_matches
from ads.client import Client
from ads.utils import flatten, _bibcode_regex_pattern

def export(*iterable, format="bibtex") -> str:
    """
    Return citation string formats for the given documents.

    :param iterable:
        An iterable that contains: :class:`ads.Document` objects, 
        :class:`ads.Library` objects, or strings of bibcodes.
            
    :param format:
        The format of the output. The options include:

        - ``ads``:        ADS (generic tagged) format 
        - ``bibtexabs``:  BibTeX + abstract
        - ``bibtex``:     BibTeX format [default]
        - ``endnote``:    EndNote format
        - ``MEDLARS``:    MEDLARS format
        - ``ProCite``:    ProCite format
        - ``RefWorks``:   RefWorks format
        - ``RIS``:        RIS (Refman) format
        - ``aastex``:     AASTeX format
        - ``Icarus``:     Icarus format
        - ``MNRAS``:      Monthly Notices of the Royal Astronomical Society format
        - ``SoPH``:       Solar Physics (SoPh) format
        - ``dcxml``:      Dublin Core (DC) XML format
        - ``refxml``:     REF-XML format
        - ``refabsxml``:  REFABS-XML format
        - ``votable``:    VOTables format
        - ``csl``:        Custom style and format
        - ``custom``:     Custom format
        - ``ieee``:       IEEE export (Unicode-encoded)
    """

    api_end_points = (
        "ads", "bibtexabs", "bibtex", "endnote", "MEDLARS", "ProCite", "RefWorks", "RIS", 
        "aastex", "Icarus", "MNRAS", "SoPH", 
        "dcxml", "refxml", "refabsxml", "votable", 
        "csl", "custom", "ieee"
    )
    # Find the format with the right cApItAlIzAtIoN
    _format = format.lower()
    for api_end_point in api_end_points:
        if api_end_point.lower() == _format:
            break
    else:
        close_matches = [f"'{m}'" for m in get_close_matches(format, api_end_points)]
        dym_string = ""
        if close_matches:
            dym_string += f"Did you mean {' or '.join(close_matches)}?\n\n"
        raise ValueError(
            f"Unknown format '{format}'. {dym_string}"
            f"All available formats: {', '.join(api_end_points)}. "
        )

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

    # TODO: What's the difference with csl and custom? 
    # And I think the docs need updating with what fields are needed here.
    # Email the ADS team about it.

    # What is the difference with GET /export/rss/{bibcode}
    # and GET /export/rss/{bibcode}/{link} ?
    # Email the ADS team about this.

    with Client() as client:
        response = client.api_request(
            f"/export/{api_end_point}", 
            method="post", 
            data=json.dumps(dict(bibcode=bibcode))
        )
    return response.json["export"]

