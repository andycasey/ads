# coding: utf-8

""" Utilities for interacting with NASA's ADS """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

# Standard library
import os

# Third party
import requests

__all__ = ["get_dev_key", "get_api_settings", "unique_preserved_list"]

def get_dev_key():
    """Retrieves the API key for ADS Labs."""

    ads_dev_key_filename = os.path.abspath(os.path.expanduser("~/.ads/dev_key"))

    if os.path.exists(ads_dev_key_filename):
        with open(ads_dev_key_filename, 'r') as fp:
            dev_key = fp.readline().rstrip()

        return dev_key

    if "ADS_DEV_KEY" in os.environ:
        return os.environ["ADS_DEV_KEY"]

    raise IOError("no ADS API key found in ~/.ads/dev_key and no ADS_DEV_KEY "\
        "environment variable found")


def get_api_settings(developer_api_key=None):
    """Gets the API settings for the developer key provided."""

    if developer_api_key is None:
        developer_api_key = get_dev_key()
        
    r = requests.get("http://labs.adsabs.harvard.edu/adsabs/api/settings/",
        params={"dev_key": developer_api_key})
    if not r.ok: r.raise_for_status()

    return r.json()


def pythonify_metrics_json(metrics):
    """
    Converts JSON-style metrics information to native Python objects.

    :param metrics:
        A metrics result from the ADS API, which includes results as colon-
        separated strings.

    :type metrics:
        dict

    :returns:
        A dictionary containing metrics results with :class:`numpy.arrays`
        instead of strings.

    :rtype:
        dict
    """

    metrics = metrics.copy()
    for key in metrics.keys():
        if key.endswith("_histogram") or key.endswith("_series"):
            branch = metrics[key]
            for sub_key in branch.keys():
                try:
                    branch[sub_key] = map(float, branch[sub_key].split(":"))
                except (ValueError, TypeError):
                    continue
                metrics[key] = branch
    return metrics


def unique_preserved_list(original_list):
    """Return a list of unique values in the same order as the original list."""
    
    seen = set()
    seen_add = seen.add
    return [x for x in original_list if x not in seen and not seen_add(x)]
