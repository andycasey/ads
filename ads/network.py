# coding: utf-8

""" Visualize network components. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard libary
import json

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


def export(articles, attribute, structure="nested", article_repr=None, new_branch_func=None,
    end_branch_func=None, **kwargs):
    """Export the article network attributes (e.g. either references or citations) for the
    given articles.

    Inputs
    ------
    articles : `Article` or list of `Articles`
        The articles to build the network with.

    attribute : "citations" or "references"
        The attribute to build the network with.

    structure : "nested" or "flat"
        Whether to return a nested or flat structure.

    article_repr : callable, optional
        A callable function to represent the article for each node.

    new_branch_func : callable, optional
        A callable function to represent each sub branch.

    end_branch_func : callable, optional
        A callable function to represent the end of a branch.
    """

    if attribute not in ("citations", "references"):
        raise ValueError("attribute must be either 'citations' or 'references'")

    if structure not in ("nested", "flat"):
        raise ValueError("structure must be either 'flat' or 'nested'")

    if article_repr is None:
        article_repr = lambda x: x

    if new_branch_func is None:
        new_branch_func = lambda x, y: {x: y}

    if end_branch_func is None:
        end_branch_func = lambda x: x

    flat_data = []

    def recursive_walk(articles, flat_data):
        branch = []

        if not isinstance(articles, (list, tuple)):
            articles = [articles]

        for article in articles:
            if hasattr(article, "_{attribute}".format(attribute=attribute)):
                # New branch
                new_branch = new_branch_func(
                    article_repr(article),
                    recursive_walk(getattr(article, "_{attribute}"
                        .format(attribute=attribute)), flat_data))

                branch.append(new_branch)
                flat_data.append(new_branch)

            else:
                # Branch end
                end_branch = end_branch_func(article_repr(article))

                branch.append(end_branch)
                flat_data.append(end_branch)

        return branch

    tree_data = recursive_walk(articles, flat_data)
    data = tree_data if structure == "nested" else flat_data

    return json.dumps(data, **kwargs)


# These functions below are just temporary and are immediately deprecated
def export_to_d3rt(paper, attribute="citations", map_func=None):
    """Export the paper provided to a JSON-format for D3.js Reingold-Tilford Tree visualisations."""

    if map_func is None:
        map_func = lambda x: x
    

    def map_as_children(articles):
        branch = []

        if not isinstance(articles, (list, tuple)):
            articles = [articles]

        for article in articles:
            if hasattr(article, "_{attribute}".format(attribute=attribute)):
                branch.append({
                    "name": map_func(article),
                    "children": map_as_children(getattr(article, "_{attribute}".format(attribute=attribute)))
                    })
            else:
                branch.append({
                    "name": map_func(article)
                    })

        return branch

    return map_as_children(paper)



def export_to_d3_heb(paper, attribute="citations", map_func=None):

    if map_func is None:
        map_func = lambda x: x

    data = []

    def map_flat(articles, data):

        if not isinstance(articles, (list, tuple)):
            articles = [articles]

        for article in articles:
            if hasattr(article, "_{attribute}".format(attribute=attribute)):
                data.append({
                    "name": map_func(article),
                    "imports": map(map_func, getattr(article, "_{attribute}".format(attribute=attribute))),
                    "size": article.citation_count
                    })

                map_flat(getattr(article, "_{attribute}".format(attribute=attribute)), data)

            else:
                # Check to see it's not a double up.
                if map_func(article) in [item["name"] for item in data]:
                    continue

                # Find out who cited this
                data.append({
                    "name": map_func(article),
                    "size": article.citation_count,
                    "imports": []
                    })

    map_flat(paper, data)
    
    # Sort the data
    data = sorted(data, key=lambda x: x["name"])

    # Do the backlinks lazily
    for item in data:
        
        if len(item["imports"]) == 0:
            imports = []
            for sub_item in data:
                if item["name"] in sub_item["imports"]:
                    imports.append(item["name"])

            item["imports"] = imports


    return data

