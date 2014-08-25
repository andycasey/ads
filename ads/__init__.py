
# coding: utf-8

""" A Python tool for interacting with NASA's ADS """

__author__ = "Andy Casey <andy@astrowizici.st>"
__version__ = "0.0.809"

import network
from core import query, metrics, metadata, retrieve_article

# ads.core.search will be deprecated in future
# You should use ads.core.query instead
from core import search
