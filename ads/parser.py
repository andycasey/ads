# coding: utf-8

""" Parsing inputs into a payload. """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

# Standard library
import datetime
import time
    
# Module specific
from utils import API_MAX_ROWS

__all__ = ['rows', 'ordering', 'dates', 'start']


def query(query, authors, dates):

    if query is None:
        # With great power comes great responsibility.
        return " *"

    # Regex match for a date range?

    # Assume rest is author/title interpreted?
    return query


def affiliation(affiliation):
    """Creates a parser based on the affiliation input."""

    if affiliation is None: return

    try:
        affiliation = str(affiliation)
    except TypeError:
        raise TypeError("affiliation must be a string-type")

    query_refinement = " aff:\"{affiliation}\"".format(affiliation=affiliation)
    return query_refinement


def rows(start, rows):
    """Checks that the number of rows provided is valid."""

    if rows == "all" or rows > API_MAX_ROWS:
        # We may have to run multiple queries here
        start, rows = 0, API_MAX_ROWS

    else:

        try:
            start = int(start)
        except TypeError:
            raise TypeError("start must be an integer-like type")

        if start < 0:
            raise ValueError("start must be positive")

        try: rows = int(rows)
        except TypeError:
            raise TypeError("rows must be an integer-like type")

        if rows < 1:
            raise ValueError("rows must be a positive integer")

    return start, rows


def ordering(sort, order):
    """Checks that the ordering and sorting inputs are valid."""

    sort, order = sort.lower(), order.lower()

    if order not in ('asc', 'desc'):
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
            .format(acceptable_sorts=', '.join(acceptable_sorts.keys())))

    if sort not in acceptable_sorts:
        for key in acceptable_sorts:
            if sort in acceptable_sorts[key]:
                sort = key
                break

    return (sort, order)


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
                " be as '(start, end)', either of which can be empty")

        if len(input_dates) == 1:
            start_date, end_date = (input_dates[0], "*")

        else:
            start_date, end_date = input_dates

        start_date = _date(start_date, default_month=1)
        end_date = _date(end_date, default_month=12)

    elif isinstance(input_dates, (str, unicode)):

        # We will accept '2002-', '2002..', '..2003', '2002..2003'
        # '2002/01..2002/08', '2002/04..', '2002/07', '2002-7', '2002-07

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
            else:
                date = _date(int(input_dates), output_format="%Y")

            start_date, end_date = date, date

    elif isinstance(input_dates, (int, float)):

        # Is there a month component as a fractional?
        if input_dates % 1 > 0:
            date = _date("{year:.0f}/{month:.0f}"
                .format(year=int(input_dates), month=(input_dates % 1)*100))

        else:
            date = _date(int(input_dates), output_format="%Y")

        start_date, end_date = date, date

    else:
        raise TypeError("date type not understood")

    if "*" not in (start_date, end_date) and start_date > end_date:
        raise ValueError("start date ({start_date}) is after the end date ({end_date})"
            .format(start_date=start_date, end_date=end_date))

    # Build query
    query_refinement = " pubdate:[{start_date} TO {end_date}]".format(
        start_date=start_date, end_date=end_date)

    return query_refinement

