# coding: utf-8

""" Utilities for interacting with NASA's ADS system. """

from __future__ import division, print_function

__author__ = "Andy Casey <acasey@mso.anu.edu.au>"

# Standard library
import os

__all__ = ['get_dev_key']

def get_dev_key():
    with open(os.path.abspath(os.path.expanduser('~/.ads/dev_key')), 'r') as fp:
        dev_key = fp.readline().rstrip()

    return dev_key