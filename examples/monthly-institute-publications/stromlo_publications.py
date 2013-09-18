# coding: utf-8

""" Retrieve all the publications with authors or co-authors from a particular institute
    in a given month. 

    In this example we will find all the publications authored (at least in part) by
    researchers at the Australian National University, Canberra."""

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
from time import localtime

# Module specific
import ads

if __name__ == "__main__":

    # Let's do it for *last* month
    current_time = localtime()

    # Just grab the last month (there are more Pythonic ways to do this)
    year = current_time.tm_year - 1 if current_time.tm_mon == 1 else current_time.tm_year
    month = current_time.tm_mon - 1 if current_time.tm_mon > 1 else 12
    
    # The affiliation string to search for
    my_affiliation = "Australian National University"

    # Get all the articles
    articles = ads.search(
        affiliation=my_affiliation,
        filter="database:astronomy AND property:refereed,
        dates="{start_year}/{start_month}..{end_year}/{end_month}"
            .format(start_year=year, start_month=month, end_year=current_time.tm_year, end_month=current_time.tm_mon),
        rows=5)

    # Let's do something interesting with the data first
    # We'll sort all the articles by first-authors with our matched affiliation first.
    sorted_articles = sorted(articles,
        key=lambda article: [(my_affiliation.lower() in affiliation.lower()) for affiliation in article.aff].index(True))

    # Great! Now let's actually do something real with these articles
    # At Mount Stromlo Observatory (the Research School of Astronomy & Astrophysics within
    # the Australian National University), we have a "monthly papers" board that shows the
    # first page of every paper published by someone at Stromlo within the last month.

    # Let's download each paper for our papers board and save them by their bibliography code.
    [ads.retrieve_article(article, output_filename="{bibcode}.pdf".format(bibcode=article.bibcode)) for article in sorted_articles]

    # If we have the pyPdf module installed, let's put together a new PDF file that just has
    # the first page from each article. Otherwise, we'll just finish this example quietly.

    try:
        from pyPdf import PdfFileReader, PdfFileWriter

    except ImportError:
        # Finished!
        _ = ''

    else:
        summary_pdf = PdfFileWriter()

        open_files = []
        for article in sorted_articles:
            filename = "{bibcode}.pdf".format(bibcode=article.bibcode)

            if not os.path.exists(filename):
                print("Did not add {filename} to the summary file because it does not exist."
                    .format(filename=filename))
                continue

            with open(filename, "rb") as fp:
                article_pdf = PdfFileReader(fp)

                # Get the first page of the article and append it to
                # our summary PDF
                summary_pdf.addPage(article_pdf.getPage(0))

        # Save the summary PDF
        with open("summary.pdf", "wb") as fp:
            fp.write(summary_pdf)

    finally:
        print("There were {num} articles published by astronomy researchers from the {my_affiliation} last month."
            .format(num=len(articles), my_affiliation=my_affiliation))
