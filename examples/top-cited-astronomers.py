# coding: utf-8

""" Who are the most cited astronomers? """

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

import ads

# Let's assume the most cited people have the most cited papers, since we can only search for papers, not people
most_cited_papers = ads.search(sort="citations", filter="database:astronomy", rows=200)

# Who are these successful people, anyways?
successful_astronomers = [paper.author[0] for paper in most_cited_papers]

# Okay, let's get the top 200 most-cited papers for each person and see how many citations they have in total
total_citations = {}
for astronomer in successful_astronomers:
    papers = ads.search("^{0}".format(astronomer.encode("utf-8")),
        sort="citations", filter="database:astronomy", rows=200)
    total_citations[astronomer] = sum([paper.citation_count for paper in papers])

# Now there's a problem because astronomers publish under "Aaronson, A" and "Aaronson, Aaron". Ugh!
duplicate_astronomers = []
for astronomer in total_citations.keys():
    # Look out for "Groups" or "Teams"
    if "," not in astronomer and total_citations[astronomer] == 0:
        print("{0} looks like a group without any citations, so we're going to delete this item.".format(astronomer))
        duplicate_astronomers.append(astronomer)
        continue

    try:
        last_name, first_name = astronomer.split(", ")[:2]
        short_name = "{0}, {1}.".format(last_name.encode("utf-8"), first_name[0])
    # What if Cher (or another mononym) writes an astronomy paper?
    except ValueError:
        last_name = astronomer.split(", ")[0]
        short_name = "{0}".format(last_name.encode("utf-8"))

    # Is this a short name?
    if astronomer == short_name: continue

    # Does this astronomer publish under a short name too?
    if short_name in total_citations.keys():
        print("{0} is a shorter version of {1}, so we're counting their citations together".format(
            short_name, astronomer))
        total_citations[astronomer] += total_citations[short_name]
        duplicate_astronomers.append(short_name)

# Delete the duplicates
for duplicate_astronomer in set(duplicate_astronomers):
    del total_citations[duplicate_astronomer]
print("\nAfter duplicates, we have the top {0} cited astronomers!".format(len(total_citations)))

# Let's sort them and just get the top 100
most_successful_astronomers = sorted(total_citations, key=total_citations.get, reverse=True)[:100]

# Voila!
for i, astronomer in enumerate(most_successful_astronomers, 1):
    print("{0}. {1} with {2} total citations".format(i, astronomer.encode("utf-8"), total_citations[astronomer]))
