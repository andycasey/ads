# coding: utf-8

""" Compile publication data for astronomy journals over the last 10 years. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json

# Module specific
import ads

if __name__ == "__main__":

    # Let's select the years and journals we want to compare
    years = (1993, 2013)
    journals = [ # (Scraped from Wikipedia)
    #    "AIAA Journal",
        "Astrobiology",
        "Astronomical Journal",
        "Astronomical Review",
    #    "Astronomische Nachrichten",
        "Astronomy and Astrophysics",
    #    "Astronomy and Computing",
    #    "Astronomy & Geophysics",
        "Astronomy Letters",
        "Astronomy Now",
        "Astronomy Reports",
        "Astroparticle Physics",
        "The Astrophysical Journal",
    #    "The Astrophysical Journal Letters",
        "The Astrophysical Journal Supplement Series",
        "Astrophysics and Space Science",
        "Celestial Mechanics and Dynamical Astronomy",
        "Classical and Quantum Gravity",
    #    "Connaissance des Temps",
        "Cosmic Research",
    #    "Earth, Moon, and Planets",
        "Earth and Planetary Science Letters",
        "General Relativity and Gravitation",
        "Geophysical Research Letters",
        "Icarus",
        "International Astronomical Union Circular",
        "International Journal of Astrobiology",
        "Journal of the British Interplanetary Society",
        "Journal of Cosmology",
        "Journal of Cosmology and Astroparticle Physics",
        "Journal of Geophysical Research",
    #    "Journal for the History of Astronomy",
    #    "Journal of the Korean Astronomical Society",
    #    "Journal of the Royal Astronomical Society of Canada",
    #    "Meteoritics & Planetary Science",
        "Monthly Notices of the Royal Astronomical Society",
    #    "Nature Geoscience",
        "New Astronomy",
        "The Observatory",
        "Planetary and Space Science",
    #    "Publications of the Astronomical Society of Japan",
        "Publications of the Astronomical Society of the Pacific",
        "Solar Physics",
        "Space Science Reviews",
        ]

    publication_data = []
    for journal in journals:

        # Initiate the dictionary for this journal
        journal_data = {
            "name": journal,
            "articles": [],
            "total": 0
        }

        for year in range(years[0], years[1] + 1):
            
            # Perform the query
            # We actually don't want all the results, we just want the metadata
            # which tells us how many publications there were
            q = ads.SearchQuery(q="pub:\"{journal}\" year:{year}".format(journal=journal, year=year), fl=['id'], rows=1)
            q.execute()

            num = int(q.response.numFound)
            print("{journal} had {num} publications in {year}"
                  .format(journal=journal, num=num, year=year))

            # Save this data
            journal_data["articles"].append([year, num])
            journal_data["total"] += num

        # Let's only save it if there were actually any publications
        if journal_data["total"] > 0:
            publication_data.append(journal_data)

    sorted_publication_data = []
    totals = [journal["total"] for journal in publication_data]
    indices = sorted(range(len(totals)),key=totals.__getitem__)
    for index in indices:
        sorted_publication_data.append(publication_data[index])

    # Save the data
    with open('journal-publications.json', 'w') as fp:
        json.dump(sorted_publication_data, fp, indent=2)
