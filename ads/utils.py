from collections.abc import Iterable

def parse_bibcode(bibcode):
    """
    Parse a bibcode and return a dictionary with the parsed data.

    See https://ui.adsabs.harvard.edu/help/actions/bibcode

    :param bibcode:
    :return:
    """

    #YYYYJJJJJVVVVMPPPPA
    items = [
        ("year", 4),
        ("bibcode", 5),
        ("volume", 4),
        ("qualifier", 1),
        ("page", 4),
        ("first_letter_of_last_name", 1)
    ]
    s, parsed = (0, dict())
    for key, length in items:
        parsed[key] = bibcode[s:s+length].strip(".")
        s += length
    return parsed


def flatten(struct):
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