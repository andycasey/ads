# coding: utf-8

""" Utilities for interacting with NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <andy@astrowizici.st>"

# Standard library
import os

# Third party
import requests

ADS_HOST = "http://adslabs.org/adsabs/api"
API_MAX_ROWS = 200

__all__ = ["get_dev_key", "get_api_settings", "ADS_HOST", "API_MAX_ROWS"]


def get_dev_key():
    """Retrieves the API key for ADS Labs."""

    ads_dev_key_filename = os.path.abspath(os.path.expanduser('~/.ads/dev_key'))

    if os.path.exists(ads_dev_key_filename):
        with open(ads_dev_key_filename, 'r') as fp:
            dev_key = fp.readline().rstrip()

        return dev_key

    if 'ADS_DEV_KEY' in os.environ:
        return os.environ['ADS_DEV_KEY']

    raise IOError("no ADS API key found in ~/.ads/dev_key")


def get_api_settings(developer_api_key):
    """Gets the API settings for the developer key provided."""

    r = requests.get("http://labs.adsabs.harvard.edu/adsabs/api/settings/", params={"dev_key": developer_api_key})
    if not r.ok: r.raise_for_status()

    return r.json()


def unique_preserved_list(original_list):
    seen = set()
    seen_add = seen.add
    return [x for x in original_list if x not in seen and not seen_add(x)]
