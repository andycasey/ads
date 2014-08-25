# coding: utf-8

""" Parsing inputs into a payload """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

# Standard library
import datetime
import time

__all__ = ["rows", "ordering", "dates", "start"]

def query(query, title, author):
    """
    Format a query for the ADS API.

    :param query: [optional]
        The query to perform.

    :type query:
        str

    :param title: [optional]
        The title of the paper to search for.

    :type title:
        str

    :param author: [optional]
        The author name to search for.

    :type author:
        str

    :returns:
        A search string that is recognised by the ADS API.

    :rtype:
        str
    """

    query_refinement = ""

    if query is not None:
        query_refinement += query

    else:
        query_refinement += " * "

    if author is not None:
        query_refinement += " author:\"{0}\"".format(author)

    if title is not None:
        query_refinement += " title:\"{0}\"".format(title)

    return query_refinement.strip() + " "


def acknowledgements(acknowledgement=None):
    """
    Creates an API-compatible parser based on the acknowledgement input.

    :param acknowledgement: [optional]
        The acknowledgement string to search for.

    :type acknowledgement:
        str

    :returns:
        An acknowledgement search string that is recognised by the ADS API.

    :rtype:
        str
    """

    if acknowledgement is None: return
    try:
        acknowledgement = str(acknowledgement)
    except TypeError:
        raise TypeError("acknowledgement must be a string-type")
    return " ack:({0})".format(acknowledgement)


def affiliation(affiliation=None, pos=None):
    """
    Creates a parser based on the affiliation input.

    :param affiliation: [optional]
        The affiliation string to search for.

    :type affiliation:
        str

    :param pos: [optional]
        The position of the affiliation to search from. If None is given then
        all positions will be searched for. Otherwise you can specify an
        integer (e.g., 1 indicating only search for affiliation of first-author),
        or a two-length tuple indicating lower and upper author-positions to
        search for.

    :type pos:
        int or 2-length tuple of int

    :returns:
        An affiliation search string that is recognised by the ADS API.

    :rtype:
        str
    """

    if affiliation is None: return

    try:
        affiliation = str(affiliation)
    except (TypeError, ValueError):
        raise TypeError("affiliation must be a string-type")

    query_refinement = "aff:({affiliation})".format(affiliation=affiliation)
    
    if pos is not None:
        # Can be any of the following:
        # int-type
        # list/tuple type of 2 int-types
        try:
            pos = int(pos)
        except (TypeError, ValueError):

            if not isinstance(pos, (list, tuple)):
                raise TypeError("affiliation position must be an integer or "\
                    "list-type of up to two integers")

            try:
                pos = map(int, pos)
            except (TypeError, ValueError):
                raise TypeError("affiliation position must be an integer or "\
                    "list-type of up to two integers")

            if len(pos) == 1:
                query_refinement = "pos({0}, {1:.0f})".format(
                    query_refinement, pos[0])

            elif len(pos) == 2:
                if pos[0] >= pos[1]:
                    raise ValueError("affiliation position range is out of order")
                query_refinement = "pos({0}, {1:.0f}, {2:.0f})".format(
                    query_refinement, pos[0], pos[1])

            else:
                raise TypeError("affiliation position must be an integer or "\
                    "list-type of up to two integers")

        else:
            query_refinement = "pos({0}, {1:.0f})".format(query_refinement, pos)
    return " " + query_refinement


def database(database=None):
    """
    Filters search results by database.

    :param database: [optional]
        The database to search within.

    :type database:
        str

    :returns:
        A database filter string that is recognised by the ADS API.

    :rtype:
        str

    :raises ValueError:
        If the databases listed in ``database`` are not 'general', 'physics', or
        'astronomy'.
    """

    if database is None: return
    database = database.lower().split(" or ")
    for each in database:
        if each not in ("general", "astronomy", "physics"):
            return ValueError("database must be either general, astronomy, or physics")
    return " OR ".join(["database:{0}".format(each) for each in database])


def ordering(sort, order):
    """Checks that the ordering and sorting inputs are valid."""

    try: sort, order = map(str, [sort, order])
    except (TypeError, ValueError):
        raise TypeError("sort and order must be string-like objects")

    sort, order = sort.lower(), order.lower()

    if order not in ("asc", "desc"):
        raise ValueError("order must be either 'asc' or 'desc'")

    acceptable_sorts = {
        "date": "time",
        "relevance": "relevance",
        "cited": "citations",
        "popularity": "popular"
    }

    if sort not in acceptable_sorts \
    and sort not in acceptable_sorts.values():
        raise ValueError("sort must be one of: {acceptable_sorts}"
            .format(acceptable_sorts=", ".join(acceptable_sorts.keys())))

    if sort not in acceptable_sorts:
        for key in acceptable_sorts:
            if sort in acceptable_sorts[key]:
                sort = key
                break

    return (sort, order)


def properties(properties=None):
    """Produces filters based on article properties """

    if properties is None: return

    available_properties = "ARTICLE, REFEREED, NOT_REFEREED, INPROCEEDINGS,"\
        " OPENACCESS, NONARTICLE, EPRINT, BOOK, PROCEEDINGS, CATALOG, SOFTWARE"
    available_properties_list = map(str.lower, available_properties.split(", "))

    if isinstance(properties, str):
        properties = (properties, )

    all_strings = lambda _: isinstance(_, str)
    if not all(map(all_strings, properties)):
        raise TypeError("properties must be a string or list-type of strings")

    if not all([each.lower() in available_properties_list for each in properties]):
        raise ValueError("available properties are {0}".format(available_properties))

    return " property:({0})".format(",".join(properties))


def rows(start, rows, max_rows=200):
    """Checks that the number of rows provided is valid."""

    try: rows = int(rows)
    except:
        if rows != "all":
            raise TypeError("rows must be an integer-type or 'all'")

    if rows == "all" or rows > max_rows:
        # We may have to run multiple queries here
        start, rows = 0, max_rows

    else:

        try:
            start = int(start)
        except (TypeError, ValueError):
            raise TypeError("start must be an integer-like type")

        if start < 0:
            raise ValueError("start must be positive")

        if rows < 1:
            raise ValueError("rows must be a positive integer")

    return start, rows


def _date(date_str, default_month=None, output_format="%Y-%m"):
    """Parses a date input into the preferred format for ADS."""

    if date_str in (None, "*"): return "*"

    date_str = str(date_str)
    formats = ("%Y", "%Y-%m", "%Y-%m-%d", "%Y/%m", "%Y/%m/%d")

    time_struct = None
    for i, format in enumerate(formats):
        try:
            time_struct = time.strptime(date_str, format)
        
        except ValueError:
            pass

        else:
            break

    if i == 0 and default_month is not None:
        time_struct = time.strptime("{year}-{month:.0f}"
            .format(year=time_struct.tm_year, month=default_month), "%Y-%m")
        
    if time_struct is None:
        raise ValueError("cannot parse date string '{date_str}'"
            .format(date_str=date_str))

    return time.strftime(output_format, time_struct)
    

def dates(input_dates):
    """Parses the input dates and returns a filter to append to the
    current query if the date range is restricted."""


    if input_dates is None: return

    if isinstance(input_dates, (list, tuple)):
        if len(input_dates) > 2:
            raise ValueError("if dates is specified as a list, it must"
                " be as (start, end), either of which can be empty")

        if len(input_dates) == 1:
            start_date, end_date = (input_dates[0], "*")

        else:
            start_date, end_date = input_dates

        start_date = _date(start_date, default_month=1)
        end_date = _date(end_date, default_month=12)

    elif isinstance(input_dates, (str, unicode)):

        # We will accept "2002-", "2002..", "..2003", "2002..2003"
        # "2002/01..2002/08", "2002/04..", "2002/07", "2002-7", "2002-07

        if input_dates.endswith("-") or input_dates.endswith(".."):
            start_date = _date(input_dates.strip("-."), default_month=1)
            end_date = "*"

        elif input_dates.startswith("-") or input_dates.startswith(".."):
            start_date = "*"
            end_date = _date(input_dates.strip("-."), default_month=12)

        elif ".." in input_dates:
            start_date, end_date = input_dates.split("..")

            if len(end_date) == 2:
                end_date = start_date[:2] + end_date

            start_date = _date(start_date, default_month=1)
            end_date = _date(end_date, default_month=12)

        else:
            if "/" in input_dates or "-" in input_dates:
                date = _date(input_dates)
                start_date, end_date = date, date

            else:
                start_date = _date("{year:.0f}-1".format(year=int(input_dates)))
                end_date = _date("{year:.0f}-12".format(year=int(input_dates)))
        
    elif isinstance(input_dates, (int, float)):

        # Is there a month component as a fractional?
        if input_dates % 1 > 0:
            date = _date("{year:.0f}/{month:.0f}"
                .format(year=int(input_dates), month=(input_dates % 1)*100))
            start_date, end_date = date, date

        else:
            start_date = _date("{year:.0f}-1".format(year=int(input_dates)))
            end_date = _date("{year:.0f}-12".format(year=int(input_dates)))

    else:
        raise TypeError("date type not understood")

    if "*" not in (start_date, end_date) and start_date > end_date:
        raise ValueError("start date ({start_date}) is after the end date ({end_date})"
            .format(start_date=start_date, end_date=end_date))

    # Build query
    query_refinement = " pubdate:[{start_date} TO {end_date}]".format(
        start_date=start_date, end_date=end_date)

    return query_refinement

