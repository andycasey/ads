# coding: utf-8

""" Visualize network components. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

__all__ = ['nodes']


def nodes(articles, attribute, map_func=None):
    """Returns a dictionary of articles linked to each other, as
    defined by the attribute (either references or citations).

    Inputs
    ------
    articles : list of `Article` objects
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

    if map_func is None:
        map_func = lambda _: _

    def recursive_walk(articles):

        branch = []
        for article in articles:
            if hasattr(article, "_{attribute}".format(attribute=attribute)):
                branch.append({
                    map_func(article): recursive_walk(getattr(article, "_{attribute}".format(attribute=attribute)))
                    })

            else:
                branch.append(map_func(article))

        return branch

    if not isinstance(articles, (list, tuple)):
        articles = [articles]

    return recursive_walk(articles)


