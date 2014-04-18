# coding: utf-8

""" Test ADS queries """

__author__ = "Andy Casey <andy@astrowizici.st>"

import unittest
import ads


def test_api_key():
    ads.utils.get_api_settings()