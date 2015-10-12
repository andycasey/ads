"""
Retrieve all articles authored by ANU RSAA researchers in the previous month.
"""

__author__ = 'Andy Casey <arc@ast.cam.ac.uk>'

# You will also need PyPDF2 (use `pip install pypdf2`) for this example in order
# to manipulate PDFs.

# Example usage:    python stromlo.py           (to run previous month)
#                   python stromlo.py 2015 8    (to specify the month)

import sys
from StringIO import StringIO
from time import localtime

import ads
import requests
from PyPDF2 import (PdfFileReader, PdfFileWriter)


def get_pdf(article, debug=False):
    """
    Download an article PDF from arXiv.

    :param article:
        The ADS article to retrieve.

    :type article:
        :class:`ads.search.Article`

    :returns:
        The binary content of the requested PDF.
    """

    print('Retrieving {0}'.format(article))

    identifier = [_ for _ in article.identifier if 'arXiv' in _]
    if identifier:
        url = 'http://arXiv.org/pdf/{0}.{1}'.format(identifier[0][9:13],
            ''.join(_ for _ in identifier[0][14:] if _.isdigit()))
    else:
        # No arXiv version. Ask ADS to redirect us to the journal article.
        params = {
            'bibcode': article.bibcode,
            'link_type': 'ARTICLE',
            'db_key': 'AST'
        }
        url = requests.get('http://adsabs.harvard.edu/cgi-bin/nph-data_query', 
            params=params).url

    q = requests.get(url)
    if not q.ok:
        print('Error retrieving {0}: {1} for {2}'.format(
            article, q.status_code, url))
        if debug: q.raise_for_status()
        else: return None

    # Check if the journal has given back forbidden HTML.
    if q.content.endswith('</html>'):
        print('Error retrieving {0}: 200 (access denied?) for {1}'.format(
            article, url))
        return None
    return q.content


def summarise_pdfs(pdfs):
    """
    Collate the first page from each of the PDFs provided into a single PDF.

    :param pdfs:
        The contents of several PDF files.

    :type pdfs:
        list of str

    :returns:
        The contents of single PDF, which can be written directly to disk.
    """

    # Ignore None.
    print('Summarising {0} articles ({1} had errors)'.format(
        len(pdfs), pdfs.count(None)))
    pdfs = [_ for _ in pdfs if _ is not None]

    summary = PdfFileWriter()
    for pdf in pdfs:
        summary.addPage(PdfFileReader(StringIO(pdf)).getPage(0))
    return summary




if __name__ == '__main__':

    # Use year/month if given, otherwise query the previous month.
    if len(sys.argv) >= 3:
        year, month = map(int, (sys.argv[1:3]))
    else:
        now = localtime()
        year, month = (now.tm_year, now.tm_mon - 1)
        if 1 > month: year, month = (year - 1, month)

    print('Querying {0} / {1}'.format(year, month))

    # Retrieve all the articles published last month.
    articles = ads.SearchQuery(
        q='aff:"Australian National University" database:astronomy '\
            'property:refereed pubdate:{0}-{1}'.format(year, month),
            fl=['id', 'first_author', 'year', 'bibcode', 'identifier'],
            sort='read_count desc')

    # Download all articles from ArXiv.
    pdfs = map(get_pdf, articles)

    # Collate the first page of each PDF into a summary PDF.
    with open('{0:d}-{1:02d}.pdf'.format(year, month), 'wb') as fp:
        summarise_pdfs(pdfs).write(fp)

