# coding: utf-8

""" Test citation tree. """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

# Standard library
import os

# Module imports
from ads import search, network

def test_citation_tree():

    output_filename = "citation-tree.json"

    paper = list(search("^Casey, A", sort="citations", order="desc", rows=1))[0]

    paper.build_citation_tree(depth=3)

    network.export(paper, "citations", output_filename,
        article_repr=lambda article: article.author[0],
        new_branch_repr=lambda article, branch: {"name": article.author[0], "children": branch},
        end_branch_repr=lambda article: {"name": article.author[0]},
        indent=2, clobber=True)

    if os.path.exists(output_filename):
        os.unlink(output_filename)

