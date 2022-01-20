
""" The ADS resolver service. """

from ads import Document
from ads.client import Client
from ads.utils import to_bibcode, parse_bibcode
from difflib import get_close_matches

def external_resources(document: Document) -> dict:
    """
    Return links to external resources, such as a publisher's full text, data links, etc., for a given document.

    :param document:
        The document to resolve external resources for.
    
    :returns:
        A list of dictionaries that describe all external resources.
    """
    bibcode = to_bibcode(document)

    with Client() as client:
        response = client.api_request(f"/resolver/{bibcode}")
    return response.json["links"]["records"]


def external_resource(document: Document, link_type: str) -> dict:
    """
    Return a specific external resource for a given document.

    :param document:
        The document to resolve external resources for.
    
    :param link_type: The type of resource to return. Available values for ``link_type`` are:
    
            - ``abstract`` Abstract
            - ``citations`` Citations to the Article
            - ``references`` References in the Article
            - ``coreads`` Also-Read Articles
            - ``toc`` Table of Contents
            - ``openurl``
            - ``metrics``
            - ``graphics``
            - ``esource`` Full text sources
                - ``pub_pdf`` Publisher PDF
                - ``eprint_pdf`` Arxiv eprint
                - ``author_pdf`` Link to PDF page provided by author
                - ``ads_pdf`` ADS PDF
                - ``pub_html`` Electronic on-line publisher article (HTML)
                - ``eprint_html`` Arxiv article
                - ``author_html`` Link to HTML page provided by author
                - ``ads_scan`` ADS scanned article
                - ``gif`` backward compatibility similar to /ads_scan
                - ``preprint`` backward compatibility similar to /eprint_html
                - ``ejournal`` backward compatibility similar to /pub_html
            - ``data`` On-line data
                - ``aca`` Acta Astronomica Data Files
                - ``alma`` Atacama Large Millimeter/submillimeter Array
                - ``ari`` Astronomisches Rechen-Institut
                - ``astroverse`` CfA Dataverse
                - ``atnf`` Australia Telescope Online Archive
                - ``author`` Author Hosted Dataset
                - ``bavj`` Data of the German Association for Variable Stars
                - ``bicep2`` BICEP/Keck Data
                - ``cadc`` Canadian Astronomy Data Center
                - ``cds`` Strasbourg Astronomical Data Center
                - ``chandra`` Chandra X-Ray Observatory
                - ``dryad`` International Repository of Research Data
                - ``esa`` ESAC Science Data Center
                - ``eso`` European Southern Observatory
                - ``figshare`` Online Open Access Repository
                - ``gcpd`` The General Catalogue of Photometric Data
                - ``github`` Git Repository Hosting Service
                - ``gtc`` Gran Telescopio CANARIAS Public Archive
                - ``heasarc`` NASA's High Energy Astrophysics Science Archive Research Center
                - ``herschel`` Herschel Science Center
                - ``ibvs`` Information Bulletin on Variable Stars
                - ``ines`` IUE Newly Extracted Spectra
                - ``iso`` Infrared Space Observatory
                - ``jwst`` JWST Proposal Info
                - ``koa`` Keck Observatory Archive
                - ``mast`` Mikulski Archive for Space Telescopes
                - ``ned`` NASA/IPAC Extragalactic Database
                - ``nexsci`` NASA Exoplanet Archive
                - ``noao`` National Optical Astronomy Observatory
                - ``pangaea`` Digital Data Library and a Data Publisher for Earth System Science
                - ``pasa`` Publication of the Astronomical Society of Australia Datasets
                - ``pdg`` Particle Data Group
                - ``pds`` The NASA Planetary Data System
                - ``protocols`` Collaborative Platform and Preprint Server for Science Methods and Protocols
                - ``simbad`` SIMBAD Database at the CDS
                - ``spitzer`` Spitzer Space Telescope
                - ``tns`` Transient Name Server
                - ``vizier`` VizieR Catalog Service
                - ``xmm`` XMM Newton Science Archive
                - ``zenodo`` Zenodo Archive
            - ``inspire`` HEP/Spires Information
            - ``librarycatalog``
            - ``presentation`` Multimedia Presentation
            - ``associated`` Associated Articles        

    :returns:
        A dictionary that describes the external resource.
    """
    bibcode = to_bibcode(document)

    # arxiv and doi are not listed as available link types in the docs at 
    # http://adsabs.github.io/help/api/api-docs.html#get-/resolver/-bibcode-
    # but there is special mention about what to do if arxiv or doi is given..
    available_link_types = (
        "arxiv", "doi", # See above.
        "abstract", "citations", "references", "coreads", "toc", "openurl",      
        "metrics", "graphics", "esource", "pub_pdf", "eprint_pdf", "author_pdf", 
        "ads_pdf", "pub_html", "eprint_html", "author_html", "ads_scan", "gif", 
        "preprint", "ejournal", "data", "aca", "alma", "ari", "astroverse", "atnf", 
        "author", "bavj", "bicep2", "cadc", "cds", "chandra", "dryad", "esa", "eso", 
        "figshare", "gcpd", "github", "gtc", "heasarc", "herschel", "ibvs", "ines", 
        "iso", "jwst", "koa", "mast", "ned", "nexsci", "noao", "pangaea", "pasa", 
        "pdg", "pds", "protocols", "simbad", "spitzer", "tns", "vizier", "xmm", 
        "zenodo", "inspire", "librarycatalog", "presentation", "associated"
    )

    _link_type = link_type.lower()
    for link_type in available_link_types:
        if link_type.lower() == _link_type:
            break
    else:
        close_matches = [f"'{m}'" for m in get_close_matches(_link_type, available_link_types)]
        dym_string = ""
        if close_matches:
            dym_string += f"Did you mean {' or '.join(close_matches)}?\n\n"
        raise ValueError(
            f"Unknown link_type '{_link_type}'. {dym_string}"
            f"All available formats: {', '.join(available_link_types)}. "
        )    

    end_point = f"/resolver/{document.bibcode}/{link_type}"
    # See http://adsabs.github.io/help/api/api-docs.html#get-/resolver/-bibcode-/-link_type-
    if link_type == "arxiv":
        parts = parse_bibcode(document.bibcode)
        end_point += f":{parts['volume']}.{parts['page_number']}"
    elif link_type == "doi":
        end_point += f":{document.doi[0]}"

    with Client() as client:
        response = client.api_request(end_point)
    return response.json
    
