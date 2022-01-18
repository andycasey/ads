import os
import json
import re
from collections import OrderedDict

from collections.abc import Iterable

_bibcode_regex_pattern = "(?P<year>[0-9]{4})(?P<journal_abbreviation>[A-Za-z0-9\&\.]{5})(?P<volume>[0-9\.]{4})(?P<qualifier>[ELPQ-Z0-9\.])(?P<page_number>[0-9\.]{4})(?P<first_letter_of_last_name>[A-Z])"


def parse_bibcode(bibcode: str) -> dict:
    """
    Parse a bibcode and return a dictionary with the parsed data.

    See https://ui.adsabs.harvard.edu/help/actions/bibcode

    """
    match = re.match(_bibcode_regex_pattern, bibcode)
    if not match:
        raise ValueError(f"Invalid bibcode '{bibcode}'")

    items = {}
    for key, value in match.groupdict().items():
        items[key] = value.strip(".")
    
    # If the qualifier is an integer, then it's the page number.
    if items["qualifier"].isdigit():
        items["page_number"] = items["qualifier"] + items["page_number"]
        items["qualifier"] = ""

    # Parse information like qualifiers?
    return items



def flatten(struct: Iterable) -> list:
    """
    Create a flat list of all items in the structure.    
    """
    if struct is None:
        return []
    flat = []
    if isinstance(struct, dict):
        for _, result in struct.items():
            flat += flatten(result)
        return flat
    if isinstance(struct, str):
        return [struct]

    try:
        # if iterable
        iterator = iter(struct)
    except TypeError:
        return [struct]

    for result in iterator:
        flat += flatten(result)
    return flat


def to_bibcode(iterable):
    """
    Return a bibcode for each item in the iterable. 
    
    The iterable could contain :class:`ads.Document` objects, bibcode strings, etc.
    """
    
    if isinstance(iterable, str):
        assert len(iterable) == 19, "All bibcodes are 19 characters long."
        return iterable
    elif isinstance(iterable, Iterable):
        return list(map(to_bibcode, iterable))
    else:
        try:
            return iterable.bibcode
        except AttributeError:
            raise TypeError("Expected a bibcode string, an ads.Document, or an iterable of these.")


def _get_data_path(basename=""):
    from ads import __path__
    return os.path.realpath(os.path.join(__path__[0], "../data", basename))

def setup_database():
    """ Set up the local database for Journals and Affiliations. """

    from ads.models.local import (database, database_path)
    from ads.models.affiliation import Affiliation
    from ads.models.journal import Journal

    ads_dir = os.path.dirname(database_path)
    data_dir = _get_data_path()

    print(f"Using ADS directory {ads_dir}")
    print(f"Looking for data files in {data_dir}")

    # Create the directory if it doesn't exist.
    os.makedirs(ads_dir, exist_ok=True)

    print(f"Remove existing database at {database_path}..")
    try:
        os.remove(database_path)
    except:
        None

    # Create the databases.
    print(f"Create database")
    database.connect()
    print(f"Create tables..")
    database.create_tables([Affiliation, Journal])
    database.close()

    _journals_path = _get_data_path("journals.json")
    _affiliation_path = _get_data_path("affiliations.tsv")
    _affiliation_country_path = _get_data_path("affiliations_country.tsv")

    print(f"Load countries from {_affiliation_country_path}..")
    
    countries_dict = OrderedDict()
    with open(_affiliation_country_path, "r") as fp:
        for line in fp.readlines()[1:]:
            country, parent_id, child_id, abbrev, canonical_affiliation = line.split("\t")
            country = country or None

            # affiliations.tsv uses "0" to indicate no ID, but affiliations_country.tsv uses ""
            parent_id, child_id = (parent_id or "0", child_id or "0")

            key = f"{parent_id}|{child_id}"
            countries_dict[key] = [country, parent_id, child_id, abbrev, canonical_affiliation]

    print(f"Loaded countries for {len(countries_dict)} affiliations.")
    print(f"Ingest affiliations from {_affiliation_path}..")

    with open(_affiliation_path, "r") as fp:
        for i, line in enumerate(fp.readlines()[1:]):
            parent_id, child_id, abbreviation, canonical_name = line.strip().split("\t")
            
            # Resolve the country with this method order
            # 1. Match by parent_id and child_id.
            # 2. Match by child_id.
            # 3. Match by parent_id.
            keys = (f"{parent_id}|{child_id}", f"|{child_id}", f"{parent_id}|")
            for key in keys:
                try:
                    country_info = countries_dict[key]
                except KeyError:
                    continue
                else:
                    country = country_info[0]
                    break
            else:
                country = None
            
            if parent_id == "0":
                parent = None

            else:
                parent = Affiliation(id=parent_id)

            Affiliation.create(
                id=child_id,
                abbreviation=abbreviation,
                canonical_name=canonical_name,
                country=country,
                parent=parent
            )

    print(f"Ingested {i + 1} affiliations")

    # Load in the journals.
    print(f"Ingest journals from {_journals_path}..")
    with open(_journals_path, "r") as fp:
        journals = json.load(fp)
    
    for j, (abbreviation, title) in enumerate(journals.items()):
        Journal.create(abbreviation=abbreviation, title=title)

    print(f"Ingested {j + 1} journals")
    print(f"Done!")
