# coding: utf-8

""" Test citation tree. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Module imports
from .. import search, network

def test_citation_tree():

    paper = search("^Casey, A", sort="citations", order="desc")[0]

    paper.build_citation_tree(depth=3)

    network.export(paper, "citations", "citation-tree.json",
        article_repr=lambda article: article.author[0],
        new_branch_repr=lambda article, branch: {"name": article.author[0], "children": branch},
        end_branch_repr=lambda article: {"name": article.author[0]},
        indent=2)



import ads
paper = ads.search("^Casey, A", sort="citations", order="desc")[0]

paper.build_citation_tree(depth=3)

ads.network.export(paper, "citations", "citation-tree.json",
        article_repr=lambda article: article.author[0],
        new_branch_repr=lambda article, branch: {"name": article.author[0], "children": branch},
        end_branch_repr=lambda articles: \
            [{"name": article.author[0]} for article in articles] \
            if isinstance(articles, (list, tuple)) else {"name": articles.author[0]},
        indent=2)


