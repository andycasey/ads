# coding: utf-8

""" Visualize network components. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import json
import logging

def nodes(article, attribute, map_func=None):
    """Returns a dictionary of articles linked to each other, as
    defined by the attribute (either references or citations).

    Inputs
    ------
    article : `Article` objects
        The articles with network information.

    attribute : citations or references
        The attribute build the nodes from.

    map_func : func, optional
        A callable function that takes a single `Article` object.
        If not None, this callable will be applied to every `Article`
        in the network.

    Examples
    --------
    The psuedocode below will return a paper, build a citation tree from
    it of depth 2, then return a network of how first authors cite `articles`.

        paper = ads.search("etc")
        paper.build_citation_tree(2)
        network = ads.network.nodes(paper, "citations", lambda article: article.author[0])

    """

    if not attribute in ("references", "citations"):
        raise ValueError("attribute must be either 'references' or 'citations'")

    nodes = {}

    def append_nodes(article):
        if hasattr(article, "_{attribute}".format(attribute=attribute)):

            key = article
            links = getattr(article, "_{attribute}".format(attribute=attribute))

            if map_func is not None:
                key = map_func(key)
                links = map(map_func, links)

            if article in nodes:
                nodes.extend(links)

            else:
                nodes[key] = links
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

