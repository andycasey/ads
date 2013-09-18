# coding: utf-8

""" Export the data to make a citation tree visualisation with D3. """

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

import ads

# Let's grab a paper to build a citation tree from
paper = ads.search("^Hubble, E", sort="citations", order="desc")[0]

# Build our citation tree to a depth of 2
paper.build_citation_tree(depth=2)

# Make a function that turns "Lastname, Firstname I." -> "Lastname, F"
pretty_author_name = lambda author: author.split(",")[0] + author.split(",")[1].strip()[1] + "."

# Export the network to citation-tree.json
ads.network.export(paper, "citations", "citation-tree.json",
    article_repr=lambda article: pretty_author_name(article.author[0]),
    new_branch_repr=lambda article, branch: {"name": pretty_author_name(article.author[0]), "children": branch},
    end_branch_repr=lambda article: {"name": pretty_author_name(article.author[0])},
    indent=2, clobber=True)
