import os
import requests
from collections import OrderedDict

from ads import logger

_database = None
_database_path = os.path.expanduser("~/.ads/affiliations.tsv")
_country_database = None
_country_database_path = os.path.expanduser("~/.ads/affiliations_country.tsv")

class Affiliation(object):

    """ A normalized affiliation. """

    def __init__(self, child_id):
        child_id = child_id.strip()
        if child_id == "-":
            self.child_id = "-"
            self._raw = []
            self.parent_id, self.abbrev, self.canonical_affiliation = (None, None, None)
            return None
        
        global _database
        _database = _database or read_database()
        
        try:
            self._raw = _database[child_id]
        except KeyError:
            raise KeyError(
                f"No affiliation found with key {child_id}. The local affiliation database may be out of date. "
                f"Use `ads.affiliations.download()` to update the database."
            )
        
        # The affiliation structure is set so that a child_id is not unique.
        # It can have many parents. There are good reasons for this, but it
        # also means that things might get a little murky.
        self.child_id = child_id

        # For now we will just take the first seen parent.
        self.parent_id, self.abbrev, self.canonical_affiliation = self._raw[0]        
                
    def __repr__(self):
        if self.child_id == "-":
            return "-"
        else:
            return f"<Affiliation {self.child_id}: {self.canonical_affiliation}>"

    def __str__(self):
        return self.abbrev

    def __eq__(self, other):
        return self.child_id == other.child_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.child_id)

    @property
    def parents(self):
        """ The parent affiliation(s). """
        return tuple([Affiliation(parent_id) for parent_id, *_ in self._raw if parent_id != '0']) or None

    @property
    def children(self):
        """ The child affiliation(s). """
        child_ids = []
        for child_id, parents in _database.items():
            for parent_id, *_ in parents:
                if parent_id == self.child_id:
                    child_ids.append(child_id)
        return tuple([Affiliation(child_id) for child_id in child_ids]) or None
    
    @property
    def siblings(self):
        """ The sibling affiliation(s). """
        sibling_ids = []
        for parent_id, *_ in self._raw:
            if parent_id == "0": continue
            for child in Affiliation(parent_id).children:
                sibling_ids.append(child.child_id)
        return tuple([Affiliation(sibling_id) for sibling_id in set(sibling_ids).difference([self.child_id])]) or None
        
    @property
    def country(self):
        """ The country of affiliation. """
        global _country_database
        _country_database = _country_database or read_country_database()
        # TODO: Throw a warning if there are many countries with the same child ID?
        results = _country_database.get(self.child_id, [])
        countries = [country for country, *_ in results]
        if len(set(countries)) > 1:
            raise ValueError(f"Multiple countries found for {self.child_id}: {tuple(countries)}")
        return countries[0]


def read_database():
    """
    Read the affiliations from the local database.

    :return:
        A dictionary of affiliations.
    """
    if not os.path.exists(_database_path):
        download(
            remote_path="https://raw.githubusercontent.com/adsabs/CanonicalAffiliations/master/parent_child.tsv",
            local_path=_database_path,
            description="affiliation database"
        )

    affiliations = OrderedDict()
    with open(_database_path, "r") as fp:
        for line in fp.readlines()[1:]:
            parent_id, child_id, abbrev, canonical_affiliation = line.strip().split("\t")
            affiliations.setdefault(child_id, [])
            affiliations[child_id].append([parent_id, abbrev, canonical_affiliation])
    return affiliations


def read_country_database():
    """
    Read the country affiliations from the local database.
    
    :returns:
        A dictionary of affiliation identifiers and countries.
    """
    if not os.path.exists(_country_database_path):
        download(
            remote_path="https://raw.githubusercontent.com/adsabs/CanonicalAffiliations/master/country_parent_child.tsv",
            local_path=_country_database_path,
            description="affiliation country database"
        )
    
    country_database = OrderedDict()
    with open(_country_database_path, "r") as fp:
        for line in fp.readlines()[1:]:
            country, parent_id, child_id, abbrev, canonical_affiliation = line.split("\t")
            country = country or None
            country_database.setdefault(child_id, [])
            country_database[child_id].append([country, parent_id, abbrev, canonical_affiliation])
    return country_database


def download(remote_path, local_path, description="file"):
    """ Download a file. """
    logger.info(f"Downloading {description} from {remote_path} to {local_path}. This should only happen once.")
    local_dir = os.path.dirname(local_path)
    try:
        os.makedirs(local_dir, exist_ok=True)
    except:
        raise OSError(f"Cannot create directory {local_dir} to store affiliations")

    with requests.get(remote_path, stream=True) as response:
        response.raise_for_status()
        with open(local_path, "wb") as fp:
            for chunk in response.iter_content(chunk_size=8192):
                fp.write(chunk)

