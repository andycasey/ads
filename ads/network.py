# coding: utf-8

""" Visualize network components. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json
import logging

def nodes(articles, attribute):
    """Returns a dictionary of articles linked to each other, as
    defined by the attribute (either references or citations).

    Inputs
    ------
    articles : list of Article objects
        The articles with network information.

    attribute : citations or references
        The attribute build the nodes from.
    """

    if not attribute in ("references", "citations"):
        raise ValueError("attribute must be either 'references' or 'citations'")

    nodes = {}

    def append_nodes(article):
        if hasattr(article, "_{attribute}".format(attribute=attribute)):
            if article in nodes:
                nodes.extend(getattr(article, "_{attribute}".format(attribute=attribute)))

            else:
                nodes[article] = getattr(article, "_{attribute}".format(attribute=attribute))
            return True

        else:
            return False

    def recursive_append(articles):
        for article in articles:
            if append_nodes(article):
                recursive_append(getattr(article, "_{attribute}".format(attribute=attribute)))

    # This line is so that we can take either a single article, or a list of articles. A list
    # will just get flattened.
    articles = sum([[articles]], [])
    recursive_append(articles)

    return nodes

